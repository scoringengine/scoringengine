import re
import sys
import os

import pynsive

import random

from glob import glob

import signal

from scoring_engine.engine.config import Config
from scoring_engine.db import DB
from scoring_engine.models.service import Service
from scoring_engine.engine.job import Job
from scoring_engine.engine.worker_queue import WorkerQueue
from scoring_engine.engine.finished_queue import FinishedQueue


class Engine(object):

    def __init__(self, total_rounds=None, current_round=1):
        self.checks = []
        self.current_round = current_round
        self.total_rounds = total_rounds

        self.config = Config()
        self.worker_queue = WorkerQueue()
        self.worker_queue.clear()
        self.finished_queue = FinishedQueue()
        self.finished_queue.clear()

        self.checks_location = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../scoring_engine/' + self.config.checks_location)

        self.last_round = False
        self.rounds_run = 0

        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

        self.db = DB()
        self.db.connect()

        self.load_checks()

    def shutdown(self):
        print("Shutting down after this round...")
        self.last_round = True

    def add_check(self, check_obj):
        self.checks.append(check_obj)
        self.checks = sorted(self.checks, key=lambda check: check.name)

    def load_checks(self):
        sys.path.append(self.checks_location)
        print("Loading checks from " + self.checks_location)
        self.plugin_manager = pynsive.PluginManager()
        self.plugin_manager.plug_into(self.checks_location)
        checks_path = self.checks_location.split('/')[-1]

        for protocol in glob(self.checks_location + "/*"):
            protocol_name = protocol.replace(self.checks_location + '/', '')
            print("\tProtocol: " + protocol_name)
            for filename in glob(protocol + "/*.py"):
                check_filename = filename.replace(self.checks_location + '/' + protocol_name + '/', '')
                print("\t\tCheck Filename: " + check_filename)

                check_source_str = open(filename, 'r').read()
                check_classname = re.search('\nclass (\w+)', check_source_str).group(1)
                check_file_module = __import__(protocol_name + '.' + check_filename.replace('.py', ''), fromlist=[check_classname])
                check_class_attr = getattr(check_file_module, check_classname)
                print("\t\t\tCheck Classname: " + check_class_attr.name)
                self.add_check(check_class_attr)

    def check_name_to_obj(self, check_name):
        for check in self.checks:
            if check.name == check_name:
                return check
        return None

    def run(self):
        while (not self.last_round) and (self.rounds_run < self.total_rounds):
            print("Running round: " + str(self.current_round))
            self.rounds_run += 1

            services = self.db.session.query(Service).all()[:]
            random.shuffle(services)
            for service in services:
                print(service.name)
                check_class = self.check_name_to_obj(service.check_name)
                print("Adding " + str(check_class) + " to queue")
                check_obj = check_class(service)
                command_str = check_obj.command()
                job = Job(service_id=service.id, command=command_str)
                self.worker_queue.add_job(job)

            self.current_round += 1
