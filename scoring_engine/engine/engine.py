import importlib
import importlib.util
import inspect
import json
import os
import random
import re
import signal
import sys
import time
from datetime import datetime
from functools import partial
from pathlib import Path

from scoring_engine.config import config
from scoring_engine.models.service import Service
from scoring_engine.models.environment import Environment
from scoring_engine.models.check import Check
from scoring_engine.models.kb import KB
from scoring_engine.models.round import Round
from scoring_engine.models.setting import Setting
from scoring_engine.engine.job import Job
from scoring_engine.engine.execute_command import execute_command
from scoring_engine.engine.basic_check import (
    CHECK_SUCCESS_TEXT,
    CHECK_FAILURE_TEXT,
    CHECK_TIMED_OUT_TEXT,
)
from scoring_engine.logger import logger
from scoring_engine.cache_helper import update_all_cache
from scoring_engine.db import session


def engine_sigint_handler(signum, frame, engine):
    engine.shutdown()


class Engine(object):
    def __init__(self, total_rounds=0):
        self.checks = []
        self.total_rounds = total_rounds

        self.config = config
        self.checks_location = self.config.checks_location

        self.verify_settings()

        self.last_round = False
        self.rounds_run = 0

        signal.signal(signal.SIGINT, partial(engine_sigint_handler, obj=self))
        signal.signal(signal.SIGTERM, partial(engine_sigint_handler, obj=self))

        self.session = session

        self.current_round = Round.get_last_round_num()

        self.load_checks()
        self.round_running = False

    def verify_settings(self):
        settings = ["target_round_time", "worker_refresh_time", "engine_paused", "pause_duration"]
        for setting_name in settings:
            if not Setting.get_setting(setting_name):
                logger.error("Must have " + setting_name + " setting.")
                exit(1)

    def shutdown(self):
        if self.round_running:
            logger.warning("Shutting down after this round...")
        else:
            logger.warning("Shutting down now.")
        self.last_round = True

    def add_check(self, check_obj):
        self.checks.append(check_obj)
        self.checks = sorted(self.checks, key=lambda check: check.__name__)

    def load_checks(self):
        logger.debug("Loading checks source from " + str(self.checks_location))
        loaded_checks = Engine.load_check_files(self.checks_location)
        for loaded_check in loaded_checks:
            logger.debug(" Found " + loaded_check.__name__)
            self.add_check(loaded_check)

    # @staticmethod
    # def load_check_files(checks_location):
    #     checks_location_module_str = checks_location.replace("/", ".")
    #     found_check_modules = pynsive.list_modules(checks_location_module_str)
    #     found_checks = []
    #     for found_module in found_check_modules:
    #         module_obj = pynsive.import_module(found_module)
    #         for name, arg in inspect.getmembers(module_obj):
    #             if name == "BasicCheck" or name == "HTTPPostCheck":
    #                 continue
    #             elif not name.endswith("Check"):
    #                 continue
    #             found_checks.append(arg)
    #     return found_checks

    @staticmethod
    def load_check_files(checks_location):
        found_checks = []
        checks_path = Path(checks_location)

        if not checks_path.is_dir():
            raise ValueError(f"{checks_location} is not a valid directory.")

        # Iterate through the checks directory to find Python files
        for py_file in checks_path.glob("*.py"):
            module_name = py_file.stem  # Get the filename without the `.py` extension
            module_path = str(py_file.resolve())

            # Convert file path to module format (dot-separated)
            checks_location_module_str = str(checks_path.resolve()).replace("/", ".")
            relative_module_path = os.path.relpath(module_path, str(checks_path.parent))
            module_str = relative_module_path.replace("/", ".").replace(".py", "")

            # Import the module dynamically
            spec = importlib.util.spec_from_file_location(module_str, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Inspect the module to find classes ending with 'Check'
            for name, arg in inspect.getmembers(module, inspect.isclass):
                if name == "BasicCheck" or name == "HTTPPostCheck":
                    continue
                if not name.endswith("Check"):
                    continue
                found_checks.append(arg)

        return found_checks

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

    def is_last_round(self):
        return self.last_round or (self.rounds_run == self.total_rounds and self.total_rounds != 0)

    def all_pending_tasks(self, tasks):
        pending_tasks = []
        for team_name, task_ids in tasks.items():
            for task_id in task_ids:
                task = execute_command.AsyncResult(task_id)
                if task.state == "PENDING":
                    pending_tasks.append(task_id)
        return pending_tasks

    def run(self):
        if self.total_rounds == 0:
            logger.info("Running engine for unlimited rounds")
        else:
            logger.info("Running engine for {0} round(s)".format(self.total_rounds))

        while not self.is_last_round():
            if Setting.get_setting("engine_paused").value:
                pause_duration = int(Setting.get_setting("pause_duration").value)
                logger.info("Engine Paused. Sleeping for {0} seconds".format(pause_duration))
                self.sleep(pause_duration)
                continue

            self.current_round += 1
            logger.info("Running round: " + str(self.current_round))
            round_start_time = datetime.now()
            self.round_running = True
            self.rounds_run += 1

            services = self.session.query(Service).all()[:]
            random.shuffle(services)
            task_ids = {}
            for service in services:
                check_class = self.check_name_to_obj(service.check_name)
                if check_class is None:
                    raise LookupError("Unable to map service to check code for " + str(service.check_name))
                logger.debug("Adding " + service.team.name + " - " + service.name + " check to queue")
                environment = random.choice(service.environments)
                check_obj = check_class(environment)
                command_str = check_obj.command()
                job = Job(environment_id=environment.id, command=command_str)
                task = execute_command.apply_async(args=[job], queue=service.worker_queue)
                team_name = environment.service.team.name
                if team_name not in task_ids:
                    task_ids[team_name] = []
                task_ids[team_name].append(task.id)

            # This array keeps track of all current round objects
            # incase we need to backout any changes to prevent
            # inconsistent check results
            cleanup_items = []

            try:
                # We store the list of tasks in the db, so that the web app
                # can consume them and can dynamically update a progress bar
                task_ids_str = json.dumps(task_ids)
                latest_kb = KB(name="task_ids", value=task_ids_str, round_num=self.current_round)
                cleanup_items.append(latest_kb)
                self.session.add(latest_kb)
                self.session.commit()

                pending_tasks = self.all_pending_tasks(task_ids)
                while pending_tasks:
                    worker_refresh_time = int(Setting.get_setting("worker_refresh_time").value)
                    waiting_info = "Waiting for all jobs to finish (sleeping " + str(worker_refresh_time) + " seconds)"
                    waiting_info += " " + str(len(pending_tasks)) + " left in queue."
                    logger.info(waiting_info)
                    self.sleep(worker_refresh_time)
                    pending_tasks = self.all_pending_tasks(task_ids)
                logger.info("All jobs have finished for this round")

                logger.info("Determining check results and saving to db")
                round_obj = Round(number=self.current_round)
                cleanup_items.append(round_obj)
                self.session.add(round_obj)
                self.session.commit()

                # We keep track of the number of passed and failed checks per round
                # so we can report a little bit at the end of each round
                teams = {}
                # Used so we import the finished checks at the end of the round
                finished_checks = []
                for team_name, task_ids in task_ids.items():
                    for task_id in task_ids:
                        task = execute_command.AsyncResult(task_id)
                        environment = self.session.query(Environment).get(task.result["environment_id"])
                        if task.result["errored_out"]:
                            result = False
                            reason = CHECK_TIMED_OUT_TEXT
                        else:
                            if re.search(environment.matching_content, task.result["output"]):
                                result = True
                                reason = CHECK_SUCCESS_TEXT
                            else:
                                result = False
                                reason = CHECK_FAILURE_TEXT

                        if environment.service.team.name not in teams:
                            teams[environment.service.team.name] = {
                                "Success": [],
                                "Failed": [],
                            }
                        if result:
                            teams[environment.service.team.name]["Success"].append(environment.service.name)
                        else:
                            teams[environment.service.team.name]["Failed"].append(environment.service.name)

                        check = Check(service=environment.service, round=round_obj)
                        # Grab the first 35,000 characters of output so it'll fit into our TEXT column,
                        # which maxes at 2^32 (65536) characters
                        check.finished(
                            result=result,
                            reason=reason,
                            output=task.result["output"][:35000],
                            command=task.result["command"],
                        )
                        finished_checks.append(check)

                for finished_check in finished_checks:
                    cleanup_items.append(finished_check)
                    self.session.add(finished_check)
                self.session.commit()

            except Exception as e:
                # We got an error while writing to db (could be normal docker stop command)
                # but we gotta clean up any trace of the current round so when we startup
                # again, we're at a consistent state
                logger.error("Error received while writing check results to db")
                logger.exception(e)
                logger.error("Ending round and cleaning up the db")
                for cleanup_item in cleanup_items:
                    try:
                        self.session.delete(cleanup_item)
                        self.session.commit()
                    except Exception:
                        pass
                sys.exit(1)

            logger.info("Finished Round " + str(self.current_round))
            logger.info("Round Duration " + str((datetime.now() - round_start_time).seconds) + " seconds")
            logger.info("Round Stats:")
            for team_name in sorted(teams):
                stat_string = " " + team_name
                stat_string += " Success: " + str(len(teams[team_name]["Success"]))
                stat_string += ", Failed: " + str(len(teams[team_name]["Failed"]))
                if len(teams[team_name]["Failed"]) > 0:
                    stat_string += " (" + ", ".join(teams[team_name]["Failed"]) + ")"
                logger.info(stat_string)

            logger.info("Updating Caches")
            update_all_cache()

            self.round_running = False

            if not self.is_last_round():
                target_round_time = int(Setting.get_setting("target_round_time").value)
                round_duration = (datetime.now() - round_start_time).seconds
                round_delta = target_round_time - round_duration
                if round_delta > 0:
                    logger.info(
                        f"Targetting {target_round_time} seconds per round. Sleeping " + str(round_delta) + " seconds"
                    )
                    self.sleep(round_delta)
                else:
                    logger.warning(
                        f"Service checks lasted {abs(round_delta)}s longer than round length ({target_round_time}s). Starting next round immediately"
                    )

        logger.info("Engine finished running")
