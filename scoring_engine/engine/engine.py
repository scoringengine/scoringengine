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
from scoring_engine.engine.worker_queue import WorkerQueue
from scoring_engine.engine.finished_queue import FinishedQueue


def engine_sigint_handler(signum, frame, engine):
    engine.shutdown()


class Engine(object):

    def __init__(self, total_rounds=0):
        self.checks = []
        self.total_rounds = total_rounds

        self.config = config
        self.worker_queue = WorkerQueue()
        self.worker_queue.clear()
        self.finished_queue = FinishedQueue()
        self.finished_queue.clear()
        self.checks_location = self.config.checks_location
        self.checks_class_list = self.config.checks_class_list

        self.last_round = False
        self.rounds_run = 0

        signal.signal(signal.SIGINT, partial(engine_sigint_handler, obj=self))
        signal.signal(signal.SIGTERM, partial(engine_sigint_handler, obj=self))

        self.db = DB()
        self.db.connect()

        self.current_round = Round.get_last_round_num() + 1

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
            check_file_module = importlib.import_module(self.checks_location + '.' + check)
            check_class_attr = getattr(check_file_module, check.upper() + 'Check')
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

    def run(self):
        self.worker_queue.clear()
        self.finished_queue.clear()
        while (not self.last_round) and (self.rounds_run < self.total_rounds or self.total_rounds == 0):
            print("Running round: " + str(self.current_round))
            self.rounds_run += 1

            services = self.db.session.query(Service).all()[:]
            random.shuffle(services)
            num_jobs_queued = 0
            for service in services:
                check_class = self.check_name_to_obj(service.check_name)
                print("Adding " + service.team.name + ' - ' + service.name + " to queue")
                environment = random.choice(service.environments)
                check_obj = check_class(environment)
                command_str = check_obj.command()
                job = Job(environment_id=environment.id, command=command_str)
                self.worker_queue.add_job(job)
                num_jobs_queued += 1
            while self.finished_queue.size() != num_jobs_queued:
                print("Waiting for all jobs to finish")
                self.sleep(20)

            round_obj = Round(number=self.current_round)
            self.db.save(round_obj)
            while self.finished_queue.size() != 0:
                print("Saving finished job...")
                finished_job = self.finished_queue.get_job()
                environment = self.db.session.query(Environment).get(finished_job.environment_id)
                if re.search(environment.matching_regex, finished_job.output):
                    result = True
                else:
                    result = False
                check = Check(service=environment.service, round=round_obj, result=result, output=finished_job.output)
                self.db.save(check)
            if not self.last_round:
                print("Sleeping in between rounds")
                self.sleep(60)
                self.current_round += 1
