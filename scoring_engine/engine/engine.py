import importlib
import random
import signal
import time
import re
import json
from functools import partial
from scoring_engine.engine.config import config
from scoring_engine.db import DB
from scoring_engine.models.service import Service
from scoring_engine.models.environment import Environment
from scoring_engine.models.check import Check
from scoring_engine.models.kb import KB
from scoring_engine.models.round import Round
from scoring_engine.engine.job import Job
from scoring_engine.engine.execute_command import execute_command
from scoring_engine.logger import logger


def engine_sigint_handler(signum, frame, engine):
    engine.shutdown()


class Engine(object):

    def __init__(self, total_rounds=0, round_time_sleep=180, worker_wait_time=30):
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
        self.round_running = False

    def shutdown(self):
        if self.round_running:
            logger.warn("Shutting down after this round...")
        else:
            logger.warn("Shutting down now.")
        self.last_round = True

    def add_check(self, check_obj):
        self.checks.append(check_obj)
        self.checks = sorted(self.checks, key=lambda check: check.__name__)

    def load_checks(self):
        logger.debug("Loading checks source from " + str(self.checks_location))
        for check in self.checks_class_list:
            check_file_module = __import__(self.checks_location, fromlist=[check])
            check_file_module = importlib.import_module(self.checks_location + '.' + check.lower())
            check_class_attr = getattr(check_file_module, check + 'Check')
            logger.debug(" Found " + check_class_attr.__name__)
            self.add_check(check_class_attr)

    def check_name_to_obj(self, check_name):
        for check in self.checks:
            if check.__name__ == check_name:
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

    def all_pending_tasks(self, tasks):
        pending_tasks = []
        for team_name, task_ids in tasks.items():
            for task_id in task_ids:
                task = execute_command.AsyncResult(task_id)
                if task.state == 'PENDING':
                    pending_tasks.append(task_id)
        return pending_tasks

    def run(self):
        while (not self.last_round) and (self.rounds_run < self.total_rounds or self.total_rounds == 0):
            self.current_round += 1
            logger.info("Running round: " + str(self.current_round))
            self.round_running = True
            self.rounds_run += 1

            services = self.db.session.query(Service).all()[:]
            random.shuffle(services)
            task_ids = {}
            for service in services:
                check_class = self.check_name_to_obj(service.check_name)
                if check_class is None:
                    raise LookupError("Unable to map service to check code for " + str(service.check_name))
                logger.debug("Adding " + service.team.name + ' - ' + service.name + " check to queue")
                environment = random.choice(service.environments)
                check_obj = check_class(environment)
                command_str = check_obj.command()
                job = Job(environment_id=environment.id, command=command_str)
                task = execute_command.delay(job)
                team_name = environment.service.team.name
                if team_name not in task_ids:
                    task_ids[team_name] = []
                task_ids[team_name].append(task.id)

            # We store the list of tasks in the db, so that the web app
            # can consume them and can dynamically update a progress bar
            task_ids_str = json.dumps(task_ids)
            latest_kb = KB(name='task_ids', value=task_ids_str, round_num=self.current_round)
            self.db.save(latest_kb)

            pending_tasks = self.all_pending_tasks(task_ids)
            while pending_tasks:
                waiting_info = "Waiting for all jobs to finish (sleeping " + str(self.worker_wait_time) + " seconds)"
                waiting_info += " " + str(len(pending_tasks)) + " left in queue."
                logger.info(waiting_info)
                self.sleep(self.worker_wait_time)
                pending_tasks = self.all_pending_tasks(task_ids)
            logger.info("All jobs have finished for this round")

            logger.info("Determining check results and saving to db")
            round_obj = Round(number=self.current_round)
            self.db.save(round_obj)

            # We keep track of the number of passed and failed checks per round
            # so we can report a little bit at the end of each round
            teams = {}
            for team_name, task_ids in task_ids.items():
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

                    if environment.service.team.name not in teams:
                        teams[environment.service.team.name] = {
                            "Success": [],
                            "Failed": [],
                        }
                    if result:
                        teams[environment.service.team.name]['Success'].append(environment.service.name)
                    else:
                        teams[environment.service.team.name]['Failed'].append(environment.service.name)

                    check = Check(service=environment.service, round=round_obj)
                    check.finished(result=result, reason=reason, output=task.result['output'], command=task.result['command'])
                    self.db.save(check)

            logger.info("Finished Round " + str(self.current_round))
            logger.info("Round Stats:")
            for team_name in sorted(teams):
                stat_string = " " + team_name
                stat_string += " Success: " + str(len(teams[team_name]['Success']))
                stat_string += ", Failed: " + str(len(teams[team_name]['Failed']))
                if len(teams[team_name]['Failed']) > 0:
                    stat_string += ' ' + str(teams[team_name]['Failed'])
                logger.info(stat_string)

            self.round_running = False

            if not self.last_round:
                logger.info("Sleeping in between rounds (" + str(self.round_time_sleep) + " seconds)")
                self.sleep(self.round_time_sleep)
