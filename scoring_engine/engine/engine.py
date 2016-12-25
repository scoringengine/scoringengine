import importlib
import random
import signal
import time
import re
from functools import partial
from scoring_engine.engine.config import config
from scoring_engine.db import DB
from scoring_engine.models.service import Service
from scoring_engine.models.environment import Environment
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.engine.job import Job
from scoring_engine.engine.execute_command import execute_command


def engine_sigint_handler(signum, frame, engine):
    engine.shutdown()


class Engine(object):

    def __init__(self, total_rounds=0, round_time_sleep=60, worker_wait_time=20):
        self.checks = []
        self.total_rounds = total_rounds
        self.round_time_sleep = round_time_sleep
        self.worker_wait_time = worker_wait_time
        self.config = config
        self.checks_location = self.config.checks_location
        self.checks_class_list = self.config.checks_class_list

        self.last_round = False
        self.rounds_run = 0

        signal.signal(signal.SIGINT, partial(engine_sigint_handler, obj=self))
        signal.signal(signal.SIGTERM, partial(engine_sigint_handler, obj=self))

        self.db = DB()
        self.db.connect()

        self.current_round = Round.get_last_round_num()

        self.load_checks()

    def shutdown(self):
        print("Shutting down after this round...")
        self.last_round = True

    def add_check(self, check_obj):
        self.checks.append(check_obj)
        self.checks = sorted(self.checks, key=lambda check: check.name)

    def load_checks(self):
        for check in self.checks_class_list:
            check_file_module = __import__(self.checks_location, fromlist=[check])
            check_file_module = importlib.import_module(self.checks_location + '.' + check.lower())
            check_class_attr = getattr(check_file_module, check + 'Check')
            print("\t\t\tCheck Classname: " + check_class_attr.name)
            self.add_check(check_class_attr)

    def check_name_to_obj(self, check_name):
        for check in self.checks:
            if check.name == check_name:
                return check
        return None

    def sleep(self, seconds):
        try:
            time.sleep(seconds)
        except Exception:
            self.shutdown()
            pass

    def is_last_round(self):
        return (not self.last_round) and (self.rounds_run < self.total_rounds or self.total_rounds == 0)

    def is_all_tasks_finished(self, tasks):
        all_tasks_finished = True
        for task_id in tasks:
            task = execute_command.AsyncResult(task_id)
            if task.state == 'PENDING':
                all_tasks_finished = False
        return all_tasks_finished

    def run(self):
        while (not self.last_round) and (self.rounds_run < self.total_rounds or self.total_rounds == 0):
            self.current_round += 1
            print("Running round: " + str(self.current_round))
            self.rounds_run += 1

            services = self.db.session.query(Service).all()[:]
            random.shuffle(services)
            task_ids = []
            for service in services:
                check_class = self.check_name_to_obj(service.check_name)
                print("Adding " + service.team.name + ' - ' + service.name + " to queue")
                environment = random.choice(service.environments)
                check_obj = check_class(environment)
                command_str = check_obj.command()
                job = Job(environment_id=environment.id, command=command_str)
                task = execute_command.delay(job)
                task_ids.append(task.id)

            while not self.is_all_tasks_finished(task_ids):
                print("Waiting for all jobs to finish")
                self.sleep(self.worker_wait_time)

            print("All tasks finished, now saving all to db")
            round_obj = Round(number=self.current_round)
            self.db.save(round_obj)
            for task_id in task_ids:
                task = execute_command.AsyncResult(task_id)
                environment = self.db.session.query(Environment).get(task.result['environment_id'])
                if task.result['errored_out']:
                    result = False
                    reason = 'Task Timed Out'
                else:
                    if re.search(environment.matching_regex, task.result['output']):
                        result = True
                        reason = "Successful Content Match"
                    else:
                        result = False
                        reason = 'Unsuccessful Content Match'
                check = Check(service=environment.service, round=round_obj)
                check.finished(result=result, reason=reason, output=task.result['output'])
                self.db.save(check)

            if not self.last_round:
                print("Sleeping in between rounds")
                self.sleep(self.round_time_sleep)
