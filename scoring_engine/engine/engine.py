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

from flask import current_app
from sqlalchemy.orm import selectinload

from scoring_engine.cache_helper import update_all_cache
from scoring_engine.config import config
from scoring_engine.db import db
from scoring_engine.engine.basic_check import CHECK_FAILURE_TEXT, CHECK_SUCCESS_TEXT, CHECK_TIMED_OUT_TEXT
from scoring_engine.engine.execute_command import execute_command
from scoring_engine.engine.job import Job
from scoring_engine.logger import logger
from scoring_engine.models.check import Check
from scoring_engine.models.environment import Environment
from scoring_engine.models.kb import KB
from scoring_engine.models.round import Round
from scoring_engine.models.property import Property
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting


def engine_sigint_handler(signum, frame, engine):
    engine.shutdown()


class Engine(object):
    def __init__(self, total_rounds=0):
        self.checks = []
        self.total_rounds = total_rounds

        self.config = config
        self.checks_location = self.config.checks_location

        # Keep reference to db for backward compatibility
        self.db = db

        self.verify_settings()

        self.last_round = False
        self.rounds_run = 0

        signal.signal(signal.SIGINT, partial(engine_sigint_handler, engine=self))
        signal.signal(signal.SIGTERM, partial(engine_sigint_handler, engine=self))

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
        self._check_map = {check.__name__: check for check in self.checks}

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
        if not hasattr(self, "_check_map"):
            self._check_map = {check.__name__: check for check in self.checks}
        return self._check_map.get(check_name)

    def sleep(self, seconds):
        try:
            time.sleep(seconds)
        except Exception:
            self.shutdown()

    def is_last_round(self):
        return self.last_round or (self.rounds_run == self.total_rounds and self.total_rounds != 0)

    def all_pending_tasks(self, tasks, completed=None):
        """Return list of task IDs still in PENDING state.

        Args:
            tasks: dict of team_name -> [task_id, ...]
            completed: optional set of already-completed task IDs to skip
        """
        if completed is None:
            completed = set()
        pending_tasks = []
        for team_name, task_ids in tasks.items():
            for task_id in task_ids:
                if task_id in completed:
                    continue
                task = execute_command.AsyncResult(task_id)
                if task.state == "PENDING":
                    pending_tasks.append(task_id)
                else:
                    completed.add(task_id)
        return pending_tasks

    def run(self):
        if self.total_rounds == 0:
            logger.info("Running engine for unlimited rounds")
        else:
            logger.info("Running engine for {0} round(s)".format(self.total_rounds))

        while not self.is_last_round():
            # End any stale transaction so MySQL REPEATABLE READ gets a
            # fresh snapshot.  Without this, the pause loop would hold an
            # open transaction and never see the updated engine_paused value.
            self.db.session.rollback()

            if Setting.get_setting("engine_paused").value:
                pause_duration = int(Setting.get_setting("pause_duration").value)
                logger.info("Engine Paused. Sleeping for {0} seconds".format(pause_duration))
                self.sleep(pause_duration)
                continue

            # Re-sync round counter from DB (handles rollback while paused or between rounds)
            db_round = Round.get_last_round_num()
            if db_round < self.current_round:
                logger.warning(
                    "Round rollback detected: engine was at round %d, DB says %d. Re-syncing.",
                    self.current_round,
                    db_round,
                )
                self.current_round = db_round

            self.current_round += 1
            logger.info("Running round: " + str(self.current_round))
            round_start_time = datetime.now()
            self.round_running = True
            self.rounds_run += 1

            # Eager-load environments, properties, and accounts to avoid N+1 queries.
            # Service.team is already lazy="joined" so it comes for free.
            services = self.db.session.query(Service).options(
                selectinload(Service.environments).selectinload(Environment.properties),
                selectinload(Service.accounts),
            ).all()[:]
            logger.info("Loaded %d services from database", len(services))
            random.shuffle(services)
            jitter_max = self.config.task_jitter_max_delay
            task_ids = {}
            task_env_map = {}  # task_id -> environment_id for timeout fallback
            for service in services:
                check_class = self.check_name_to_obj(service.check_name)
                if check_class is None:
                    raise LookupError("Unable to map service to check code for " + str(service.check_name))
                logger.debug("Adding " + service.team.name + " - " + service.name + " check to queue")
                dispatch_start = time.time()
                environment = random.choice(service.environments)
                check_obj = check_class(environment)
                command_str = check_obj.command()
                job = Job(environment_id=environment.id, command=command_str)
                countdown = random.uniform(0, jitter_max) if jitter_max > 0 else 0
                task = execute_command.apply_async(args=[job], queue=service.worker_queue, countdown=countdown)
                dispatch_elapsed = time.time() - dispatch_start
                if dispatch_elapsed > 1.0:
                    logger.warning(
                        "Slow task dispatch: %s - %s took %.1fs (check=%s)",
                        service.team.name, service.name, dispatch_elapsed, service.check_name,
                    )
                team_name = environment.service.team.name
                if team_name not in task_ids:
                    task_ids[team_name] = []
                task_ids[team_name].append(task.id)
                task_env_map[task.id] = environment.id

            total_tasks = sum(len(ids) for ids in task_ids.values())
            logger.info("Dispatched %d tasks to %d team queues", total_tasks, len(task_ids))

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
                self.db.session.add(latest_kb)
                self.db.session.commit()
                logger.info("Saved task manifest to KB, waiting for workers")

                completed_tasks = set()
                pending_tasks = self.all_pending_tasks(task_ids, completed_tasks)
                round_wait_start = time.time()
                # Pre-fetch settings used in the wait loop
                target_round_time = int(Setting.get_setting("target_round_time").value)
                worker_refresh_time = int(Setting.get_setting("worker_refresh_time").value)
                # Hard ceiling: 3x the target round time or 5 minutes, whichever is greater
                max_round_wait = max(target_round_time * 3, 300)
                while pending_tasks:
                    elapsed = time.time() - round_wait_start
                    if elapsed >= max_round_wait:
                        logger.warning(
                            "Round timeout reached (%.0fs). Revoking %d stuck task(s) and proceeding.",
                            elapsed,
                            len(pending_tasks),
                        )
                        for stuck_task_id in pending_tasks:
                            execute_command.AsyncResult(stuck_task_id).revoke(terminate=True)
                        break
                    waiting_info = "Waiting for all jobs to finish (sleeping " + str(worker_refresh_time) + " seconds)"
                    waiting_info += " " + str(len(pending_tasks)) + " left in queue."
                    logger.info(waiting_info)
                    self.sleep(worker_refresh_time)
                    pending_tasks = self.all_pending_tasks(task_ids, completed_tasks)
                else:
                    logger.info("All jobs have finished for this round")

                logger.info("Determining check results and saving to db")
                round_obj = Round(round_start=round_start_time, number=self.current_round)
                cleanup_items.append(round_obj)
                self.db.session.add(round_obj)
                self.db.session.commit()

                # Pre-fetch all environments needed for result processing in one query
                all_env_ids = list(set(task_env_map.values()))
                env_query = (
                    self.db.session.query(Environment)
                    .options(selectinload(Environment.service))
                    .filter(Environment.id.in_(all_env_ids))
                    .all()
                )
                env_cache = {e.id: e for e in env_query}

                logger.info("Pre-fetched %d environments, processing task results", len(env_cache))

                # We keep track of the number of passed and failed checks per round
                # so we can report a little bit at the end of each round
                teams = {}
                processed_count = 0
                for team_name, task_ids in task_ids.items():
                    for task_id in task_ids:
                        task_start = time.time()
                        task = execute_command.AsyncResult(task_id)
                        # Fetch meta once to avoid double deserialization of large results
                        task_state = task.state
                        task_result = task.result if task_state == "SUCCESS" else None
                        task_elapsed = time.time() - task_start
                        processed_count += 1
                        if processed_count % 100 == 0:
                            logger.info("Processing results: %d/%d tasks", processed_count, total_tasks)
                        if task_elapsed > 1.0:
                            output_len = len(task_result.get("output", "")) if isinstance(task_result, dict) else 0
                            logger.warning(
                                "Slow task result fetch: task %s took %.1fs (state=%s, output_len=%d)",
                                task_id, task_elapsed, task_state, output_len,
                            )

                        # Handle stuck/revoked/failed tasks via env mapping
                        if task_result is None or not isinstance(task_result, dict):
                            env_id = task_env_map.get(task_id)
                            if env_id is None:
                                logger.warning("No result or env mapping for task %s (state=%s), skipping", task_id, task_state)
                                continue
                            environment = env_cache.get(env_id)
                            if environment is None:
                                logger.warning("Environment %s not found for timed-out task %s, skipping", env_id, task_id)
                                continue
                            logger.warning(
                                "Task %s stuck/failed (state=%s), marking %s - %s as timed out",
                                task_id, task_state, environment.service.team.name, environment.service.name,
                            )
                            result = False
                            reason = CHECK_TIMED_OUT_TEXT
                            full_output = "Task did not complete within the round time limit."
                        else:
                            environment = env_cache.get(task_result["environment_id"])
                            if environment is None:
                                logger.warning("Environment %s not found for task %s, skipping", task_result["environment_id"], task_id)
                                continue
                            full_output = task_result["output"][:5000]
                            if task_result["errored_out"]:
                                result = False
                                reason = CHECK_TIMED_OUT_TEXT
                            else:
                                try:
                                    matched = re.search(environment.matching_content, full_output)
                                except re.error:
                                    logger.warning(
                                        "Invalid regex pattern for environment %s: %r, falling back to literal match",
                                        environment.id,
                                        environment.matching_content,
                                    )
                                    matched = environment.matching_content in full_output
                                if matched:
                                    # Check reject pattern - if it matches, fail even though content matched
                                    if environment.matching_content_reject:
                                        try:
                                            rejected = re.search(environment.matching_content_reject, full_output)
                                        except re.error:
                                            logger.warning(
                                                "Invalid reject regex for environment %s: %r, falling back to literal match",
                                                environment.id,
                                                environment.matching_content_reject,
                                            )
                                            rejected = environment.matching_content_reject in full_output
                                        if rejected:
                                            result = False
                                            reason = CHECK_FAILURE_TEXT
                                        else:
                                            result = True
                                            reason = CHECK_SUCCESS_TEXT
                                    else:
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

                        # TODO: File writes disabled for performance investigation.
                        # Re-enable once Redis output cap proves sufficient.
                        # # Write full output to disk for later retrieval
                        # try:
                        #     team_name_safe = environment.service.team.name
                        #     service_name_safe = environment.service.name
                        #     output_dir = os.path.join(
                        #         self.config.check_output_folder,
                        #         team_name_safe,
                        #         service_name_safe,
                        #     )
                        #     os.makedirs(output_dir, exist_ok=True)
                        #     output_path = os.path.join(output_dir, f"round_{self.current_round}.txt")
                        #     with open(output_path, "w") as f:
                        #         f.write(full_output)
                        # except Exception as write_err:
                        #     logger.warning("Failed to write check output to disk: %s", write_err)

                        # Store 5K in DB (matches Redis MAX_OUTPUT cap)
                        command = task_result["command"] if task_result else ""
                        check.finished(
                            result=result,
                            reason=reason,
                            output=full_output[:5000],
                            command=command,
                        )
                        cleanup_items.append(check)
                        self.db.session.add(check)
                logger.info("Processed %d check results, committing to database", total_tasks)
                round_end_time = datetime.now()
                round_obj.round_end = round_end_time
                self.db.session.commit()
                logger.info("Database commit complete")

            except Exception as e:
                # We got an error while writing to db (could be normal docker stop command)
                # but we gotta clean up any trace of the current round so when we startup
                # again, we're at a consistent state
                logger.error("Error received while writing check results to db")
                logger.exception(e)
                logger.error("Ending round and cleaning up the db")
                for cleanup_item in cleanup_items:
                    try:
                        self.db.session.delete(cleanup_item)
                        self.db.session.commit()
                    except Exception:
                        pass
                sys.exit(1)

            logger.info("Finished Round " + str(self.current_round))
            logger.info("Round Duration " + str((round_end_time - round_start_time).seconds) + " seconds")
            logger.info("Round Stats:")
            for team_name in sorted(teams):
                stat_string = " " + team_name
                stat_string += " Success: " + str(len(teams[team_name]["Success"]))
                stat_string += ", Failed: " + str(len(teams[team_name]["Failed"]))
                if len(teams[team_name]["Failed"]) > 0:
                    stat_string += " (" + ", ".join(teams[team_name]["Failed"]) + ")"
                logger.info(stat_string)

            logger.info("Updating Caches")
            update_all_cache(current_app)

            # Clear session identity map to prevent bloat across rounds.
            # Without this, the session accumulates hundreds of objects per round
            # and the next Service query stalls reconciling stale state.
            self.db.session.expire_all()

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
