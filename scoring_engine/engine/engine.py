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
from datetime import datetime, timezone
from functools import partial
from pathlib import Path

from celery import states
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
from scoring_engine.models.round_score import RoundScore
from scoring_engine.models.property import Property
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting
from scoring_engine.schedule import engine_should_run
from scoring_engine.worker_packs import DEFAULT_PACK, check_pack, service_queue


def _utcnow():
    """Current time as a naive UTC datetime.

    The round timestamps must be UTC to match how they are stored/compared
    everywhere else (the round model default, the display localizers, and the
    wall-clock scoreboard freeze all assume naive UTC). Plain ``datetime.now()``
    is the container's *local* time, which only coincides with UTC when the
    container clock happens to be UTC.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def engine_sigint_handler(signum, frame, engine):
    engine.shutdown()


class Engine(object):
    # Maximum number of task ids asked of the Celery result backend in a single
    # round-trip.  Collapses thousands of per-task lookups into a handful of
    # batched calls while keeping each individual command a sane size.
    RESULT_FETCH_CHUNK_SIZE = 500

    # Lower bound for the hard ceiling on how long we wait for a round's tasks
    # to finish.  The effective ceiling is max(target_round_time * 3, this).
    ROUND_WAIT_FLOOR = 300
    # Worker tool-pack coverage (see scoring_engine/worker_packs.py). A pack
    # queue counts as covered if a worker reported it within QUEUE_SEEN_TTL, so
    # one slow broadcast reply doesn't fail a pack's checks.
    QUEUE_INSPECT_TIMEOUT = 1.0
    QUEUE_SEEN_TTL = 300

    # How many times we try to remove a partially written round before giving up
    # (and how long we wait between attempts, multiplied by the attempt number).
    CLEANUP_MAX_ATTEMPTS = 3
    CLEANUP_RETRY_DELAY = 2

    # Minimum pause between consecutive failed rounds.  The failure path
    # normally paces itself to target_round_time, but a round that fails
    # *slowly* (say, after waiting out the task ceiling) has no pacing left, and
    # retrying instantly just hammers a database that is already struggling.
    # Doubles per consecutive failure up to the cap.
    ROUND_FAILURE_BACKOFF_BASE = 5
    ROUND_FAILURE_BACKOFF_MAX = 60

    def __init__(self, total_rounds=0):
        self.checks = []
        self.total_rounds = total_rounds
        self._queue_last_seen = {}

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

        # Set to False the first time the result backend proves it cannot do
        # bulk lookups, so we stop paying for the failed attempt every poll.
        self._batch_result_fetch = True

        # A failed round is rolled back and retried rather than killing the
        # process, but only up to a point: an error that reproduces every round
        # is not a blip, and an engine that spins forever producing no rounds is
        # worse than one that crashes, because nobody notices it.
        self.consecutive_round_failures = 0
        self.max_consecutive_round_failures = max(int(self.config.max_consecutive_round_failures), 0)
        if self.max_consecutive_round_failures == 0:
            logger.warning(
                "max_consecutive_round_failures is disabled: the engine will retry failed rounds "
                "forever and never exit on its own. Watch the logs for repeated round failures."
            )

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

    def _covered_queues(self):
        """Queues some live worker consumes, or None if that can't be determined.

        Only used for tool-pack queues: if no worker serves e.g. "main.browser",
        those checks would sit in Redis until the round's hard timeout, stalling
        every round. Returns None (dispatch everything, as before) when no worker
        answers at all or the broadcast fails.
        """
        try:
            active = execute_command.app.control.inspect(timeout=self.QUEUE_INSPECT_TIMEOUT).active_queues()
        except Exception as e:
            logger.warning("Could not query worker queues: %s", e)
            active = None
        now = time.time()
        if isinstance(active, dict) and active:
            for queues in active.values():
                for queue in queues or []:
                    self._queue_last_seen[queue["name"]] = now
        if not self._queue_last_seen:
            return None
        return {name for name, seen in self._queue_last_seen.items() if now - seen < self.QUEUE_SEEN_TTL}

    def check_name_to_obj(self, check_name):
        if not hasattr(self, "_check_map"):
            self._check_map = {check.__name__: check for check in self.checks}
        return self._check_map.get(check_name)

    @staticmethod
    def _safe_regex_search(pattern, text, env_id=None, timeout=5):
        """Run re.search with a timeout to prevent ReDoS hangs.

        Uses signal.alarm on the main thread. Falls back to literal
        match if the regex takes longer than *timeout* seconds or is invalid.
        """
        def _alarm_handler(signum, frame):
            raise TimeoutError("Regex timed out")

        old_handler = signal.signal(signal.SIGALRM, _alarm_handler)
        signal.alarm(timeout)
        try:
            result = re.search(pattern, text)
        except TimeoutError:
            logger.warning(
                "Regex timed out after %ds for environment %s, pattern %r — falling back to literal match",
                timeout,
                env_id,
                pattern,
            )
            result = pattern in text
        except re.error:
            logger.warning(
                "Invalid regex pattern for environment %s: %r, falling back to literal match",
                env_id,
                pattern,
            )
            result = pattern in text
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
        return result

    def sleep(self, seconds):
        try:
            time.sleep(seconds)
        except Exception:
            self.shutdown()

    def is_last_round(self):
        return self.last_round or (self.rounds_run == self.total_rounds and self.total_rounds != 0)

    def _fetch_task_metas(self, task_ids):
        """Fetch Celery result metadata for many tasks with as few round-trips as possible.

        Returns a dict of ``task_id -> {"status": ..., "result": ...}``.  A task
        the backend has never heard of reports ``PENDING`` with no result, which
        is exactly what ``AsyncResult`` does.  ``result`` is only populated for
        ``SUCCESS`` tasks, matching the previous per-task behaviour that avoided
        deserializing payloads nobody looks at.
        """
        ordered_ids = list(dict.fromkeys(task_ids))
        if not ordered_ids:
            return {}

        if self._batch_result_fetch:
            try:
                return self._fetch_task_metas_batched(ordered_ids)
            except (AttributeError, NotImplementedError, TypeError) as e:
                # The configured result backend cannot do bulk lookups (or is a
                # stand-in that does not behave like one).  Everything else --
                # connection errors and the like -- propagates just as it did
                # when we called AsyncResult() one task at a time.
                self._batch_result_fetch = False
                logger.warning(
                    "Result backend does not support batched lookups (%s), falling back to per-task fetching",
                    e,
                )
        return self._fetch_task_metas_individually(ordered_ids)

    def _fetch_task_metas_batched(self, task_ids):
        """Read many task results out of the result backend using its bulk mget API."""
        backend = execute_command.backend
        metas = {}
        for start in range(0, len(task_ids), self.RESULT_FETCH_CHUNK_SIZE):
            end = start + self.RESULT_FETCH_CHUNK_SIZE
            chunk = task_ids[start:end]
            payloads = backend.mget([backend.get_key_for_task(task_id) for task_id in chunk])
            if not isinstance(payloads, (list, tuple)) or len(payloads) != len(chunk):
                raise TypeError(
                    "result backend mget returned {0}, expected a sequence of {1} value(s)".format(
                        type(payloads).__name__, len(chunk)
                    )
                )
            for task_id, payload in zip(chunk, payloads):
                metas[task_id] = self._meta_from_payload(backend, task_id, payload)
        return metas

    @staticmethod
    def _meta_from_payload(backend, task_id, payload):
        """Turn a raw result-backend payload into the meta dict the engine consumes."""
        if not payload:
            # Nothing stored for this task yet: it has not finished (or its
            # result already expired).  AsyncResult calls this PENDING too.
            return {"status": states.PENDING, "result": None}
        try:
            meta = backend.decode_result(payload)
        except Exception:
            # A payload we cannot deserialize is never going to become usable,
            # so treat it as a finished-but-broken task instead of waiting for
            # it until the round ceiling.
            logger.warning("Unable to decode result payload for task %s, treating it as failed", task_id)
            return {"status": states.FAILURE, "result": None}
        status = meta.get("status", states.PENDING)
        return {
            "status": status,
            "result": meta.get("result") if status == states.SUCCESS else None,
        }

    @staticmethod
    def _fetch_task_metas_individually(task_ids):
        """Per-task fallback for result backends without bulk lookups."""
        metas = {}
        for task_id in task_ids:
            task = execute_command.AsyncResult(task_id)
            status = task.state
            metas[task_id] = {
                "status": status,
                "result": task.result if status == states.SUCCESS else None,
            }
        return metas

    def all_pending_tasks(self, tasks, completed=None, metas=None):
        """Return list of task IDs still in PENDING state.

        Args:
            tasks: dict of team_name -> [task_id, ...]
            completed: optional set of already-completed task IDs to skip
            metas: optional dict, populated with the result metadata of every
                task that finished in a terminal state.  Lets the caller reuse
                what we already fetched instead of asking the backend again.
        """
        if completed is None:
            completed = set()

        to_check = []
        seen = set()
        for team_name, task_ids in tasks.items():
            for task_id in task_ids:
                if task_id in completed or task_id in seen:
                    continue
                seen.add(task_id)
                to_check.append(task_id)

        fetched = self._fetch_task_metas(to_check)

        pending_tasks = []
        for task_id in to_check:
            meta = fetched.get(task_id) or {"status": states.PENDING, "result": None}
            status = meta.get("status", states.PENDING)
            if status == states.PENDING:
                pending_tasks.append(task_id)
            else:
                completed.add(task_id)
                # Only cache terminal results.  Transient states (STARTED,
                # RETRY) still count as "not pending" -- same as before -- but
                # their meta can still change, so we re-read those later.
                if metas is not None and status in states.READY_STATES:
                    metas[task_id] = meta
        return pending_tasks

    def _cleanup_failed_round(self, round_number):
        """Remove every trace of a partially written round.

        Deletes by round number rather than by object identity: the session has
        to be rolled back first (which detaches everything we added), and doing
        it by number also catches rows that were written but never tracked.
        The deletes and the commit are a single transaction, so the round is
        either entirely gone or entirely untouched.

        Returns True when the database is known to be clean afterwards.
        """
        try:
            for attempt in range(1, self.CLEANUP_MAX_ATTEMPTS + 1):
                try:
                    self.db.session.rollback()
                    round_ids = [
                        row.id for row in self.db.session.query(Round.id).filter(Round.number == round_number).all()
                    ]
                    if round_ids:
                        # Services touched by this round, captured before its checks
                        # are deleted, so the consecutive-failure cache can be
                        # repaired from the remaining history once they are gone.
                        affected_service_ids = [
                            row[0]
                            for row in self.db.session.query(Check.service_id)
                            .filter(Check.round_id.in_(round_ids))
                            .distinct()
                            .all()
                        ]
                        self.db.session.query(Check).filter(Check.round_id.in_(round_ids)).delete(
                            synchronize_session=False
                        )
                        # Materialized scores are keyed by round; they must die with
                        # the round or the scoreboard keeps ghost points for a round
                        # that no longer exists.
                        self.db.session.query(RoundScore).filter(RoundScore.round_id.in_(round_ids)).delete(
                            synchronize_session=False
                        )
                        self.db.session.query(Round).filter(Round.id.in_(round_ids)).delete(synchronize_session=False)
                        # The deleted round's pass/fail no longer applies; rebuild
                        # the consecutive-failure cache for the services it touched
                        # from the remaining checks (rare path -- a scan is fine).
                        if affected_service_ids:
                            from scoring_engine.scores import recompute_consecutive_failures_cache

                            recompute_consecutive_failures_cache(
                                self.db.session, service_ids=affected_service_ids, commit=False
                            )
                    kb_removed = (
                        self.db.session.query(KB)
                        .filter(KB.round_num == round_number, KB.name == "task_ids")
                        .delete(synchronize_session=False)
                    )
                    self.db.session.commit()
                    logger.info("Cleaned up partially written round %d", round_number)
                    if round_ids or kb_removed:
                        self._invalidate_caches_after_cleanup(round_number)
                    return True
                except Exception as cleanup_error:
                    logger.error(
                        "Cleanup attempt %d/%d for round %d failed",
                        attempt,
                        self.CLEANUP_MAX_ATTEMPTS,
                        round_number,
                    )
                    logger.exception(cleanup_error)
                    try:
                        self.db.session.rollback()
                    except Exception:
                        logger.exception("Unable to roll back the database session while cleaning up")
                    if attempt < self.CLEANUP_MAX_ATTEMPTS:
                        self.sleep(self.CLEANUP_RETRY_DELAY * attempt)
            return False
        finally:
            # Bulk deletes do not touch the identity map, and a failed round
            # leaves half-built objects lying around.  Start the next round
            # from an empty session either way.
            self.db.session.expunge_all()

    def _invalidate_caches_after_cleanup(self, round_number):
        """Drop cached API responses that still reference the discarded round.

        The admin rollback endpoint calls ``update_all_cache`` after the exact
        same delete, and for the same reason: the scoreboard, overview and team
        endpoints are cached per-visibility, so without this the web app keeps
        serving data for a round that no longer exists until the next
        successful round refreshes it.
        """
        try:
            update_all_cache(current_app)
            logger.info("Flushed caches after discarding round %d", round_number)
        except Exception:
            # A cache problem must not mask the round failure we are already
            # handling.  The next successful round refreshes everything anyway.
            logger.exception("Unable to update caches after discarding round %d", round_number)

    def _sleep_after_failed_round(self, round_start_time, consecutive_failures=1):
        """Pace the retry after a failed round.

        Without this a sustained outage would spin the engine in a tight loop,
        dispatching a full set of tasks every time round.  We wait out the rest
        of the round window as usual, but never less than an exponential
        back-off, so a round that burned its whole window before failing still
        gives whatever broke some room to recover.
        """
        if self.is_last_round():
            return
        try:
            target_round_time = int(Setting.get_setting("target_round_time").value)
        except Exception:
            # The database is probably what failed in the first place.
            target_round_time = 60
        round_delta = target_round_time - (_utcnow() - round_start_time).seconds
        # The exponent is clamped as well as the result: with the bound
        # disabled the failure count is unbounded, and 2 ** (a few thousand) is
        # an expensive way to arrive at a number we are about to throw away.
        backoff = min(
            self.ROUND_FAILURE_BACKOFF_BASE * (2 ** min(max(consecutive_failures, 1) - 1, 16)),
            self.ROUND_FAILURE_BACKOFF_MAX,
        )
        delay = max(round_delta, backoff)
        if delay > 0:
            logger.info(
                "Sleeping %d seconds before retrying (%d consecutive failed round(s))",
                delay,
                consecutive_failures,
            )
            self.sleep(delay)

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

            # Competition schedule: outside every configured window the engine
            # idles rather than probing hosts that are powered down between
            # competition days. This gates only the *next* round, so any in-flight
            # round finishes and materializes first; the loop re-checks each cycle,
            # so the engine resumes on its own when the next window opens. No
            # windows configured means no schedule -- the engine always runs.
            if not engine_should_run(_utcnow(), session=self.db.session):
                pause_duration = int(Setting.get_setting("pause_duration").value)
                logger.info("Outside competition window. Sleeping for {0} seconds".format(pause_duration))
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
            round_start_time = _utcnow()
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
            # Checks not dispatched because no worker has their tool pack:
            # (environment_id, reason, command), recorded as failed below.
            undispatched = []
            needs_pack_queue = any(
                check_pack(self.check_name_to_obj(s.check_name)) != DEFAULT_PACK
                for s in services
                if self.check_name_to_obj(s.check_name) is not None
            )
            covered_queues = self._covered_queues() if needs_pack_queue else None
            for service in services:
                check_class = self.check_name_to_obj(service.check_name)
                if check_class is None:
                    raise LookupError("Unable to map service to check code for " + str(service.check_name))
                if not service.environments:
                    logger.warning("Skipping %s - %s: no environments configured", service.team.name, service.name)
                    continue
                logger.debug("Adding " + service.team.name + " - " + service.name + " check to queue")
                dispatch_start = time.time()
                environment = random.choice(service.environments)
                check_obj = check_class(environment)
                command_str = check_obj.command()
                job = Job(environment_id=environment.id, command=command_str, env=check_obj.command_env)
                queue = service_queue(service, check_class)
                pack = check_pack(check_class)
                if pack != DEFAULT_PACK and covered_queues is not None and queue not in covered_queues:
                    logger.warning(
                        "No worker serves queue %s; failing %s - %s (enable the '%s' worker pack)",
                        queue, service.team.name, service.name, pack,
                    )
                    reason = "No worker available for check pack '{0}' (queue {1})".format(pack, queue)
                    undispatched.append((environment.id, reason, command_str))
                    continue
                countdown = random.uniform(0, jitter_max) if jitter_max > 0 else 0
                task = execute_command.apply_async(args=[job], queue=queue, countdown=countdown)
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

            # Everything written below is tagged with self.current_round, so
            # _cleanup_failed_round() can back the whole round out by number if
            # anything goes wrong and leave the db in a consistent state.
            try:
                # We store the list of tasks in the db, so that the web app
                # can consume them and can dynamically update a progress bar
                task_ids_str = json.dumps(task_ids)
                latest_kb = KB(name="task_ids", value=task_ids_str, round_num=self.current_round)
                self.db.session.add(latest_kb)
                self.db.session.commit()
                logger.info("Saved task manifest to KB, waiting for workers")

                completed_tasks = set()
                # Result metadata harvested while polling, so the result
                # processing below does not have to ask the backend twice.
                task_metas = {}
                pending_tasks = self.all_pending_tasks(task_ids, completed_tasks, task_metas)
                round_wait_start = time.time()
                # Pre-fetch settings used in the wait loop
                target_round_time = int(Setting.get_setting("target_round_time").value)
                worker_refresh_time = int(Setting.get_setting("worker_refresh_time").value)
                # Hard ceiling: 3x the target round time or 5 minutes, whichever is greater
                max_round_wait = max(target_round_time * 3, self.ROUND_WAIT_FLOOR)
                while pending_tasks:
                    elapsed = time.time() - round_wait_start
                    if elapsed >= max_round_wait:
                        logger.warning(
                            "Round timeout reached (%.0fs). Revoking %d stuck task(s) and proceeding.",
                            elapsed,
                            len(pending_tasks),
                        )
                        # One broadcast for the whole batch instead of one per
                        # task; the worker-side revoke command takes a list.
                        execute_command.app.control.revoke(list(pending_tasks), terminate=True)
                        break
                    waiting_info = "Waiting for all jobs to finish (sleeping " + str(worker_refresh_time) + " seconds)"
                    waiting_info += " " + str(len(pending_tasks)) + " left in queue."
                    logger.info(waiting_info)
                    self.sleep(worker_refresh_time)
                    pending_tasks = self.all_pending_tasks(task_ids, completed_tasks, task_metas)
                else:
                    logger.info("All jobs have finished for this round")

                logger.info("Determining check results and saving to db")
                round_obj = Round(round_start=round_start_time, number=self.current_round)
                self.db.session.add(round_obj)
                self.db.session.commit()
                # Capture the round's PK as a plain int now, while nothing is pending
                # so the read is harmless. commit() above expired round_obj, and later
                # reading any attribute off it (even the PK) reloads the row and
                # autoflushes -- which, once checks are pending, would flush them
                # ahead of the single round-close commit and defeat the failed-round
                # handling. Use this int for materialization instead.
                round_id = round_obj.id

                # Pre-fetch all environments needed for result processing in one query
                all_env_ids = list(set(task_env_map.values()) | {env_id for env_id, _, _ in undispatched})
                env_query = (
                    self.db.session.query(Environment)
                    .options(selectinload(Environment.service))
                    .filter(Environment.id.in_(all_env_ids))
                    .all()
                )
                env_cache = {e.id: e for e in env_query}

                logger.info("Pre-fetched %d environments, processing task results", len(env_cache))

                # Anything we did not already collect while polling (revoked or
                # stuck tasks, plus whatever finished since the last poll) is
                # fetched now in a single batched pass.
                missing_task_ids = [
                    task_id
                    for team_task_ids in task_ids.values()
                    for task_id in team_task_ids
                    if task_id not in task_metas
                ]
                if missing_task_ids:
                    fetch_start = time.time()
                    task_metas.update(self._fetch_task_metas(missing_task_ids))
                    fetch_elapsed = time.time() - fetch_start
                    log = logger.warning if fetch_elapsed > 5.0 else logger.info
                    log(
                        "Fetched %d outstanding task result(s) from the result backend in %.1fs",
                        len(missing_task_ids),
                        fetch_elapsed,
                    )

                # We keep track of the number of passed and failed checks per round
                # so we can report a little bit at the end of each round
                teams = {}
                # Accumulate per-team service points for passing checks as we go, so
                # the round_score rows can be written from memory in the same commit
                # as the checks -- no extra query, and nothing that would autoflush
                # the pending checks early.
                round_points = {}
                # Per-service pass/fail for this round, accumulated in memory so
                # the consecutive-failure cache can be updated in the same commit
                # without querying the pending checks (which would autoflush them).
                round_pass_ids = set()  # services with >=1 passing check this round
                round_fail_counts = {}  # service id -> count of failing checks this round
                processed_count = 0
                for team_name, team_task_ids in task_ids.items():
                    for task_id in team_task_ids:
                        meta = task_metas.get(task_id) or {"status": states.PENDING, "result": None}
                        task_state = meta.get("status", states.PENDING)
                        task_result = meta.get("result") if task_state == states.SUCCESS else None
                        processed_count += 1
                        if processed_count % 100 == 0:
                            logger.info("Processing results: %d/%d tasks", processed_count, total_tasks)

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
                                matched = self._safe_regex_search(
                                    environment.matching_content, full_output, environment.id
                                )
                                if matched:
                                    # Check reject pattern - if it matches, fail even though content matched
                                    if environment.matching_content_reject:
                                        rejected = self._safe_regex_search(
                                            environment.matching_content_reject, full_output, environment.id
                                        )
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
                            team_id = environment.service.team_id
                            round_points[team_id] = round_points.get(team_id, 0) + environment.service.points
                            round_pass_ids.add(environment.service.id)
                        else:
                            teams[environment.service.team.name]["Failed"].append(environment.service.name)
                            sid = environment.service.id
                            round_fail_counts[sid] = round_fail_counts.get(sid, 0) + 1

                        check = Check(service=environment.service, round=round_obj)

                        # NOTE: the engine intentionally does not archive full check output to
                        # config.check_output_folder. Per-round file writes were disabled during a
                        # performance investigation and never restored, so
                        # /api/admin/check/<id>/full_output always falls back to the truncated DB
                        # copy written below. Only revisit if the 5K cap proves insufficient for
                        # operators; see git history for the removed implementation.
                        # Store 5K in DB (matches Redis MAX_OUTPUT cap)
                        command = task_result["command"] if task_result else ""
                        check.finished(
                            result=result,
                            reason=reason,
                            output=full_output[:5000],
                            command=command,
                        )
                        self.db.session.add(check)

                for env_id, reason, command in undispatched:
                    environment = env_cache[env_id]
                    teams.setdefault(environment.service.team.name, {"Success": [], "Failed": []})
                    teams[environment.service.team.name]["Failed"].append(environment.service.name)
                    sid = environment.service.id
                    round_fail_counts[sid] = round_fail_counts.get(sid, 0) + 1
                    check = Check(service=environment.service, round=round_obj)
                    check.finished(result=False, reason=reason, output=reason, command=command)
                    self.db.session.add(check)
                logger.info("Processed %d check results, committing to database", total_tasks + len(undispatched))
                round_end_time = _utcnow()
                round_obj.round_end = round_end_time

                # Materialize per-team score facts from the sums accumulated above,
                # staged into the SAME commit as the round's checks so a round and
                # its scores become visible atomically. Passing the precomputed
                # points (and clear_existing=False, since a fresh round has no prior
                # rows) means no query runs here -- nothing autoflushes the pending
                # checks ahead of this single commit.
                from scoring_engine.scores import materialize_round

                # Use the round_id/current_round ints captured earlier -- reading an
                # attribute off the (expired) round_obj here would autoflush the
                # pending checks ahead of this single commit.
                rows_written = materialize_round(
                    self.db.session,
                    round_id,
                    self.current_round,
                    points_by_team=round_points,
                    clear_existing=False,
                    commit=False,
                )

                # Fold this round's pass/fail into the materialized consecutive-
                # failure cache in the SAME commit. no_autoflush keeps the pending
                # checks from flushing early; the in-memory result sets mean no
                # checks query runs here. A round that rolls back before the commit
                # reverts these updates for free (they were never committed).
                from scoring_engine.scores import apply_consecutive_failures

                with self.db.session.no_autoflush:
                    apply_consecutive_failures(self.db.session, round_pass_ids, round_fail_counts)

                self.db.session.commit()
                logger.info("Database commit complete; materialized round scores for %d team(s)", rows_written)

            except Exception as e:
                # Something blew up part way through the round (most often a
                # database blip).  We must not leave a half-written round
                # behind -- it would score every team as if the checks we never
                # got to had failed -- but a transient error should not take the
                # whole engine down mid-competition either.  So: discard the
                # round entirely, then carry on with the next one -- up to a
                # point.  An error that reproduces round after round is not
                # transient, and quietly spinning through a competition
                # producing no rounds is worse than crashing, because nobody
                # notices it.
                self.consecutive_round_failures += 1
                logger.error(
                    "Error received while writing check results to db (consecutive failure %d)",
                    self.consecutive_round_failures,
                )
                logger.exception(e)
                logger.error("Ending round %d and cleaning up the db", self.current_round)
                if not self._cleanup_failed_round(self.current_round):
                    logger.critical(
                        "Round %d could not be cleaned up and may be partially scored. "
                        "Once the database is healthy, roll back to round %d from the admin page.",
                        self.current_round,
                        self.current_round,
                    )
                self.round_running = False
                if (
                    self.max_consecutive_round_failures
                    and self.consecutive_round_failures >= self.max_consecutive_round_failures
                ):
                    logger.error(
                        "%d consecutive round(s) have failed (limit %d). This is not a transient "
                        "problem, so the engine is exiting instead of silently producing no rounds. "
                        "Last error: %r",
                        self.consecutive_round_failures,
                        self.max_consecutive_round_failures,
                        e,
                    )
                    sys.exit(1)
                self._sleep_after_failed_round(round_start_time, self.consecutive_round_failures)
                continue

            # The round landed, so whatever went wrong before was transient.
            self.consecutive_round_failures = 0

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
                round_duration = (_utcnow() - round_start_time).seconds
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
