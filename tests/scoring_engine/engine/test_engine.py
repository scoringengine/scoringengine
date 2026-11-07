import itertools
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from celery import states
from celery.backends.redis import RedisBackend

from scoring_engine.celery_app import celery_app
from scoring_engine.db import db
from scoring_engine.engine.basic_check import BasicCheck, CHECK_SUCCESS_TEXT, CHECK_TIMED_OUT_TEXT
from scoring_engine.engine.engine import Engine, _utcnow
from scoring_engine.models.check import Check
from scoring_engine.models.environment import Environment
from scoring_engine.models.kb import KB
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team


class TestEngine:
    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        target_round_time_obj = Setting.get_setting("target_round_time")
        target_round_time_obj.value = 0
        db.session.add(target_round_time_obj)
        worker_refresh_time_obj = Setting.get_setting("worker_refresh_time")
        worker_refresh_time_obj.value = 0
        db.session.add(worker_refresh_time_obj)

        db.session.commit()

    def test_init(self):
        """Engine auto-discovers every check class in scoring_engine/checks.

        Per-check requirements (command test, docs, ...) are enforced in
        tests/scoring_engine/checks/test_check_contract.py, so adding a check
        doesn't require editing a list here.
        """
        engine = Engine()
        names = [cls.__name__ for cls in engine.checks]
        assert len(names) == len(set(names)), "Duplicate check class names"
        assert all(issubclass(cls, BasicCheck) for cls in engine.checks)
        # Guard against discovery silently breaking (e.g. a bad checks_location)
        assert len(names) >= 28
        assert "SSHCheck" in names

    def test_total_rounds_init(self):
        engine = Engine(total_rounds=100)
        assert engine.total_rounds == 100

    def test_shutdown(self):
        engine = Engine()
        assert engine.last_round is False
        engine.shutdown()
        assert engine.last_round is True

    def test_run_one_round(self):
        engine = Engine(total_rounds=1)
        assert engine.rounds_run == 0
        engine.run()
        assert engine.rounds_run == 1
        assert engine.current_round == 1

    def test_run_ten_rounds(self):
        engine = Engine(total_rounds=10)
        assert engine.current_round == 0
        assert engine.rounds_run == 0
        engine.run()
        assert engine.rounds_run == 10
        assert engine.current_round == 10

    def test_run_hundred_rounds(self):
        engine = Engine(total_rounds=100)
        assert engine.current_round == 0
        assert engine.rounds_run == 0
        engine.run()
        assert engine.rounds_run == 100
        assert engine.current_round == 100

    def test_check_name_to_obj_positive(self):
        engine = Engine()
        check_obj = engine.check_name_to_obj("ICMPCheck")
        # Compare by name: the engine imports check modules under its own module names
        assert check_obj.__name__ == "ICMPCheck"

    def test_check_name_to_obj_negative(self):
        engine = Engine()
        check_obj = engine.check_name_to_obj("Garbage Check")
        assert check_obj is None

    def test_is_last_round_unlimited(self):
        engine = Engine()
        assert engine.is_last_round() is False

    def test_is_last_round_true(self):
        engine = Engine()
        engine.last_round = True
        assert engine.is_last_round() is True

    def test_is_last_round_restricted(self):
        engine = Engine(total_rounds=1)
        engine.rounds_run = 1
        assert engine.is_last_round() is True

    @patch("scoring_engine.engine.engine.execute_command")
    def test_jitter_applies_countdown(self, mock_execute_command):
        """When task_jitter_max_delay > 0, apply_async gets a countdown > 0."""
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        service = Service(
            name="ICMP Service",
            team=team,
            check_name="ICMPCheck",
            host="127.0.0.1",
        )
        db.session.add(service)
        env = Environment(service=service, matching_content="*")
        db.session.add(env)
        db.session.commit()

        # Fake a completed async result so the engine doesn't wait forever
        mock_result = MagicMock()
        mock_result.id = "fake-task-id"
        mock_result.state = "SUCCESS"
        mock_result.result = {
            "environment_id": env.id,
            "errored_out": False,
            "output": "*",
            "command": "echo test",
        }
        mock_execute_command.apply_async.return_value = mock_result
        mock_execute_command.AsyncResult.return_value = mock_result

        engine = Engine(total_rounds=1)
        engine.config.task_jitter_max_delay = 30
        engine.run()

        call_kwargs = mock_execute_command.apply_async.call_args
        assert "countdown" in call_kwargs.kwargs
        assert 0 <= call_kwargs.kwargs["countdown"] <= 30

    @patch("scoring_engine.engine.engine.execute_command")
    def test_jitter_disabled_passes_zero_countdown(self, mock_execute_command):
        """When task_jitter_max_delay == 0 (default), countdown is 0."""
        team = Team(name="Blue Team 1", color="Blue")
        db.session.add(team)
        service = Service(
            name="ICMP Service",
            team=team,
            check_name="ICMPCheck",
            host="127.0.0.1",
        )
        db.session.add(service)
        env = Environment(service=service, matching_content="*")
        db.session.add(env)
        db.session.commit()

        mock_result = MagicMock()
        mock_result.id = "fake-task-id"
        mock_result.state = "SUCCESS"
        mock_result.result = {
            "environment_id": env.id,
            "errored_out": False,
            "output": "*",
            "command": "echo test",
        }
        mock_execute_command.apply_async.return_value = mock_result
        mock_execute_command.AsyncResult.return_value = mock_result

        engine = Engine(total_rounds=1)
        engine.config.task_jitter_max_delay = 0
        engine.run()

        call_kwargs = mock_execute_command.apply_async.call_args
        assert call_kwargs.kwargs["countdown"] == 0

    @patch("scoring_engine.engine.engine.execute_command")
    def test_many_services_many_rounds_performance(self, mock_execute_command):
        """Stress test: 50 services across 10 teams for 10 rounds (500 checks).

        Verifies the engine handles large-scale competitions without N+1
        query degradation or session bloat between rounds.
        """
        num_teams = 10
        services_per_team = 5
        num_rounds = 10

        teams = []
        envs = []
        for t in range(num_teams):
            team = Team(name=f"Blue Team {t + 1}", color="Blue")
            db.session.add(team)
            teams.append(team)
        db.session.flush()

        for team in teams:
            for s in range(services_per_team):
                service = Service(
                    name=f"Service{s}",
                    team=team,
                    check_name="ICMPCheck",
                    host=f"10.0.{team.id}.{s + 1}",
                )
                db.session.add(service)
                db.session.flush()
                env = Environment(service=service, matching_content="*")
                db.session.add(env)
                envs.append(env)
        db.session.commit()

        # Build a lookup so each apply_async call returns a unique mock result
        # keyed by environment ID
        env_results = {}
        task_counter = [0]

        def fake_apply_async(args=None, queue=None, countdown=0):
            job = args[0]
            task_counter[0] += 1
            task_id = f"task-{task_counter[0]}"
            mock_result = MagicMock()
            mock_result.id = task_id
            mock_result.state = "SUCCESS"
            mock_result.result = {
                "environment_id": job["environment_id"],
                "errored_out": False,
                "output": "*",
                "command": "echo test",
            }
            env_results[task_id] = mock_result
            return mock_result

        mock_execute_command.apply_async.side_effect = fake_apply_async
        mock_execute_command.AsyncResult.side_effect = lambda tid: env_results.get(tid, MagicMock(state="SUCCESS", result=None))

        engine = Engine(total_rounds=num_rounds)
        engine.run()

        assert engine.rounds_run == num_rounds
        assert engine.current_round == num_rounds

        # Verify all checks were created
        from scoring_engine.models.check import Check
        from scoring_engine.models.round import Round

        total_services = num_teams * services_per_team
        assert db.session.query(Round).count() == num_rounds
        assert db.session.query(Check).count() == total_services * num_rounds

    # todo figure out how to test the remaining functionality of engine
    # where we're waiting for the worker queues to finish and everything


TASK_KEY_PREFIX = "celery-task-meta-"


class FakeResultBackend:
    """Minimal stand-in for a Celery key/value result backend.

    Stores already-decoded meta dicts keyed by task id and records every
    ``mget`` call so tests can assert on the number of round-trips.
    """

    def __init__(self, metas=None):
        self.store = dict(metas or {})
        self.mget_calls = []

    def get_key_for_task(self, task_id):
        return TASK_KEY_PREFIX + task_id

    def mget(self, keys):
        keys = list(keys)
        self.mget_calls.append(keys)
        prefix_len = len(TASK_KEY_PREFIX)
        return [self.store.get(key[prefix_len:]) for key in keys]

    def decode_result(self, payload):
        return payload


def _success_meta(environment_id, output="*", command="echo test"):
    return {
        "status": "SUCCESS",
        "result": {
            "environment_id": environment_id,
            "errored_out": False,
            "output": output,
            "command": command,
        },
    }


def _make_service(team_name="Blue Team 1", service_name="ICMP Service"):
    team = db.session.query(Team).filter(Team.name == team_name).first()
    if team is None:
        team = Team(name=team_name, color="Blue")
        db.session.add(team)
    service = Service(name=service_name, team=team, check_name="ICMPCheck", host="127.0.0.1")
    db.session.add(service)
    env = Environment(service=service, matching_content="*")
    db.session.add(env)
    db.session.commit()
    return env


class TestBatchedResultFetching:
    """The engine must ask the result backend about many tasks at once."""

    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        for name in ("target_round_time", "worker_refresh_time"):
            setting = Setting.get_setting(name)
            setting.value = 0
            db.session.add(setting)
        db.session.commit()

    @patch("scoring_engine.engine.engine.execute_command")
    def test_fetch_task_metas_uses_one_backend_call(self, mock_execute_command):
        backend = FakeResultBackend(
            {
                "t1": _success_meta(7),
                "t2": {"status": "FAILURE", "result": "kaboom"},
            }
        )
        mock_execute_command.backend = backend

        engine = Engine()
        metas = engine._fetch_task_metas(["t1", "t2", "t3"])

        assert len(backend.mget_calls) == 1
        assert backend.mget_calls[0] == [
            TASK_KEY_PREFIX + "t1",
            TASK_KEY_PREFIX + "t2",
            TASK_KEY_PREFIX + "t3",
        ]
        assert metas["t1"]["status"] == "SUCCESS"
        assert metas["t1"]["result"]["environment_id"] == 7
        # Only SUCCESS tasks carry a result payload, same as before
        assert metas["t2"] == {"status": "FAILURE", "result": None}
        # A task the backend has never heard of is PENDING
        assert metas["t3"] == {"status": "PENDING", "result": None}
        mock_execute_command.AsyncResult.assert_not_called()

    @patch("scoring_engine.engine.engine.execute_command")
    def test_fetch_task_metas_chunks_large_batches(self, mock_execute_command):
        backend = FakeResultBackend()
        mock_execute_command.backend = backend

        engine = Engine()
        task_ids = ["task-{0}".format(i) for i in range(1200)]
        metas = engine._fetch_task_metas(task_ids)

        assert [len(call) for call in backend.mget_calls] == [500, 500, 200]
        assert len(metas) == 1200
        assert all(meta["status"] == "PENDING" for meta in metas.values())

    @patch("scoring_engine.engine.engine.execute_command")
    def test_fetch_task_metas_deduplicates_ids(self, mock_execute_command):
        backend = FakeResultBackend({"t1": _success_meta(1)})
        mock_execute_command.backend = backend

        engine = Engine()
        metas = engine._fetch_task_metas(["t1", "t1", "t2"])

        assert backend.mget_calls[0] == [TASK_KEY_PREFIX + "t1", TASK_KEY_PREFIX + "t2"]
        assert set(metas) == {"t1", "t2"}

    @patch("scoring_engine.engine.engine.execute_command")
    def test_undecodable_payload_is_treated_as_failed(self, mock_execute_command):
        class BrokenBackend(FakeResultBackend):
            def decode_result(self, payload):
                raise ValueError("not deserializable")

        mock_execute_command.backend = BrokenBackend({"t1": "garbage"})

        engine = Engine()
        metas = engine._fetch_task_metas(["t1"])

        # Not PENDING: a payload we cannot read will never become readable, so
        # the engine must not sit and wait for it.
        assert metas["t1"] == {"status": "FAILURE", "result": None}

    @patch("scoring_engine.engine.engine.execute_command")
    def test_all_pending_tasks_batches_across_teams(self, mock_execute_command):
        backend = FakeResultBackend(
            {
                "t1": _success_meta(1),
                "t3": {"status": "REVOKED", "result": None},
            }
        )
        mock_execute_command.backend = backend

        engine = Engine()
        tasks = {"Team1": ["t1", "t2"], "Team2": ["t3", "t4"]}
        completed = set()
        metas = {}

        pending = engine.all_pending_tasks(tasks, completed, metas)

        assert pending == ["t2", "t4"]
        assert completed == {"t1", "t3"}
        assert metas["t1"]["result"]["environment_id"] == 1
        assert metas["t3"]["status"] == "REVOKED"
        # 4 tasks across 2 teams, still a single backend round-trip
        assert len(backend.mget_calls) == 1

    @patch("scoring_engine.engine.engine.execute_command")
    def test_all_pending_tasks_only_asks_about_outstanding_tasks(self, mock_execute_command):
        backend = FakeResultBackend({"t1": _success_meta(1)})
        mock_execute_command.backend = backend

        engine = Engine()
        tasks = {"Team1": ["t1", "t2"], "Team2": ["t3"]}
        completed = set()
        metas = {}

        assert engine.all_pending_tasks(tasks, completed, metas) == ["t2", "t3"]

        backend.store["t2"] = _success_meta(2)
        assert engine.all_pending_tasks(tasks, completed, metas) == ["t3"]

        # The second poll skipped the already completed t1
        assert backend.mget_calls[1] == [TASK_KEY_PREFIX + "t2", TASK_KEY_PREFIX + "t3"]
        assert completed == {"t1", "t2"}

    @patch("scoring_engine.engine.engine.execute_command")
    def test_non_terminal_states_count_as_done_but_are_not_cached(self, mock_execute_command):
        """STARTED/RETRY are 'not PENDING' (as before) but their meta can still change."""
        backend = FakeResultBackend({"t1": {"status": "STARTED", "result": None}})
        mock_execute_command.backend = backend

        engine = Engine()
        completed = set()
        metas = {}

        assert engine.all_pending_tasks({"Team1": ["t1"]}, completed, metas) == []
        assert completed == {"t1"}
        assert "t1" not in metas

    @patch("scoring_engine.engine.engine.execute_command")
    def test_falls_back_to_async_result_when_backend_cannot_mget(self, mock_execute_command):
        class NoMgetBackend(FakeResultBackend):
            def mget(self, keys):
                raise NotImplementedError("Does not support get_many")

        mock_execute_command.backend = NoMgetBackend()
        mock_execute_command.AsyncResult.side_effect = lambda tid: MagicMock(
            state="SUCCESS", result={"task_id": tid}
        )

        engine = Engine()
        metas = engine._fetch_task_metas(["t1", "t2"])

        assert engine._batch_result_fetch is False
        assert metas["t1"] == {"status": "SUCCESS", "result": {"task_id": "t1"}}
        assert mock_execute_command.AsyncResult.call_count == 2

        # The unsupported backend is remembered - no repeat attempts
        engine._fetch_task_metas(["t3"])
        assert mock_execute_command.AsyncResult.call_count == 3

    @patch("scoring_engine.engine.engine.execute_command")
    def test_backend_errors_still_propagate(self, mock_execute_command):
        class BrokenBackend(FakeResultBackend):
            def mget(self, keys):
                raise ConnectionError("redis is gone")

        mock_execute_command.backend = BrokenBackend()

        engine = Engine()
        with pytest.raises(ConnectionError):
            engine._fetch_task_metas(["t1"])
        assert engine._batch_result_fetch is True

    @patch("scoring_engine.engine.engine.execute_command")
    def test_round_scores_results_without_per_task_lookups(self, mock_execute_command):
        envs = [_make_service(service_name="Service{0}".format(i)) for i in range(3)]
        backend = FakeResultBackend()
        mock_execute_command.backend = backend

        counter = itertools.count()

        def fake_apply_async(args=None, queue=None, countdown=0):
            job = args[0]
            task_id = "task-{0}".format(next(counter))
            backend.store[task_id] = _success_meta(job["environment_id"])
            return MagicMock(id=task_id)

        mock_execute_command.apply_async.side_effect = fake_apply_async

        engine = Engine(total_rounds=1)
        engine.run()

        assert mock_execute_command.AsyncResult.call_count == 0
        # A single poll saw everything finished, and the result processing
        # reused those metas instead of asking again.
        assert len(backend.mget_calls) == 1
        assert len(backend.mget_calls[0]) == len(envs)

        checks = db.session.query(Check).all()
        assert len(checks) == len(envs)
        assert all(check.result is True for check in checks)
        assert all(check.reason == CHECK_SUCCESS_TEXT for check in checks)

    @patch("scoring_engine.engine.engine.execute_command")
    def test_stuck_tasks_are_revoked_in_one_call_and_marked_timed_out(self, mock_execute_command):
        envs = [_make_service(service_name="Service{0}".format(i)) for i in range(3)]
        backend = FakeResultBackend()  # nothing ever completes
        mock_execute_command.backend = backend

        task_ids = []

        def fake_apply_async(args=None, queue=None, countdown=0):
            task_id = "stuck-{0}".format(len(task_ids))
            task_ids.append(task_id)
            return MagicMock(id=task_id)

        mock_execute_command.apply_async.side_effect = fake_apply_async

        engine = Engine(total_rounds=1)
        # target_round_time is 0 in this fixture, so dropping the floor makes
        # the hard ceiling trip on the first pass through the wait loop.
        engine.ROUND_WAIT_FLOOR = 0
        engine.run()

        mock_execute_command.app.control.revoke.assert_called_once()
        revoke_args, revoke_kwargs = mock_execute_command.app.control.revoke.call_args
        assert sorted(revoke_args[0]) == sorted(task_ids)
        assert revoke_kwargs["terminate"] is True

        checks = db.session.query(Check).all()
        assert len(checks) == len(envs)
        assert all(check.result is False for check in checks)
        assert all(check.reason == CHECK_TIMED_OUT_TEXT for check in checks)
        # The round still completed and was recorded
        assert db.session.query(Round).count() == 1


class TestFailedRoundRecovery:
    """A failed round must be rolled back, not kill the engine process."""

    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        for name in ("target_round_time", "worker_refresh_time"):
            setting = Setting.get_setting(name)
            setting.value = 0
            db.session.add(setting)
        db.session.commit()

    @staticmethod
    def _wire_successful_tasks(mock_execute_command):
        backend = FakeResultBackend()
        mock_execute_command.backend = backend
        counter = itertools.count()

        def fake_apply_async(args=None, queue=None, countdown=0):
            job = args[0]
            task_id = "task-{0}".format(next(counter))
            backend.store[task_id] = _success_meta(job["environment_id"])
            return MagicMock(id=task_id)

        mock_execute_command.apply_async.side_effect = fake_apply_async
        return backend

    @staticmethod
    def _break_check_commit(monkeypatch, keep_failing=False):
        """Make the commit that writes the round's checks blow up."""
        real_commit = db.session.commit
        state = {"tripped": False}

        def flaky_commit():
            if state["tripped"] and keep_failing:
                raise RuntimeError("database went away")
            if not state["tripped"] and any(isinstance(obj, Check) for obj in db.session.new):
                state["tripped"] = True
                raise RuntimeError("database went away")
            return real_commit()

        monkeypatch.setattr(db.session, "commit", flaky_commit)
        return state

    @patch("scoring_engine.engine.engine.execute_command")
    def test_failed_round_leaves_no_partial_data_and_does_not_exit(self, mock_execute_command, monkeypatch):
        _make_service()
        self._wire_successful_tasks(mock_execute_command)
        state = self._break_check_commit(monkeypatch)

        engine = Engine(total_rounds=1)
        engine.CLEANUP_RETRY_DELAY = 0
        engine.ROUND_FAILURE_BACKOFF_BASE = 0
        # Must not raise SystemExit
        engine.run()

        assert state["tripped"] is True
        assert engine.rounds_run == 1
        assert engine.round_running is False
        # Nothing at all from the failed round survives
        assert db.session.query(Round).count() == 0
        assert db.session.query(Check).count() == 0
        assert db.session.query(KB).count() == 0

    @patch("scoring_engine.engine.engine.execute_command")
    def test_engine_continues_to_next_round_after_failure(self, mock_execute_command, monkeypatch):
        _make_service()
        self._wire_successful_tasks(mock_execute_command)
        self._break_check_commit(monkeypatch)

        engine = Engine(total_rounds=2)
        engine.CLEANUP_RETRY_DELAY = 0
        engine.ROUND_FAILURE_BACKOFF_BASE = 0
        engine.run()

        assert engine.rounds_run == 2
        rounds = db.session.query(Round).all()
        # Round 1 failed and was discarded, so its number is reused
        assert [r.number for r in rounds] == [1]
        assert engine.current_round == 1
        assert db.session.query(Check).count() == 1
        assert db.session.query(KB).count() == 1

    @patch("scoring_engine.engine.engine.execute_command")
    def test_cleanup_failure_is_logged_and_engine_survives(self, mock_execute_command, monkeypatch):
        _make_service()
        self._wire_successful_tasks(mock_execute_command)
        self._break_check_commit(monkeypatch, keep_failing=True)

        engine = Engine(total_rounds=1)
        engine.CLEANUP_RETRY_DELAY = 0
        engine.ROUND_FAILURE_BACKOFF_BASE = 0

        with patch("scoring_engine.engine.engine.logger") as mock_logger:
            engine.run()
            assert mock_logger.critical.called

        assert engine.rounds_run == 1

    def test_cleanup_removes_round_checks_and_kb(self):
        env = _make_service()
        round_obj = Round(round_start=datetime.now(), number=4)
        db.session.add(round_obj)
        other_round = Round(round_start=datetime.now(), number=3)
        db.session.add(other_round)
        db.session.commit()
        db.session.add(Check(service=env.service, round=round_obj))
        db.session.add(Check(service=env.service, round=other_round))
        db.session.add(KB(name="task_ids", value="{}", round_num=4))
        db.session.add(KB(name="task_ids", value="{}", round_num=3))
        db.session.commit()

        engine = Engine()
        assert engine._cleanup_failed_round(4) is True

        assert [r.number for r in db.session.query(Round).all()] == [3]
        assert db.session.query(Check).count() == 1
        assert [kb.round_num for kb in db.session.query(KB).all()] == [3]

    def test_cleanup_is_a_noop_when_nothing_was_written(self):
        engine = Engine()
        assert engine._cleanup_failed_round(99) is True

    @patch("scoring_engine.engine.engine.update_all_cache")
    def test_cleanup_invalidates_web_caches(self, mock_update_all_cache):
        """The web app must not keep serving data for a round we just deleted."""
        env = _make_service()
        round_obj = Round(round_start=datetime.now(), number=4)
        db.session.add(round_obj)
        db.session.commit()
        db.session.add(Check(service=env.service, round=round_obj))
        db.session.add(KB(name="task_ids", value="{}", round_num=4))
        db.session.commit()

        engine = Engine()
        assert engine._cleanup_failed_round(4) is True

        assert mock_update_all_cache.call_count == 1

    @patch("scoring_engine.engine.engine.update_all_cache")
    def test_cleanup_does_not_flush_caches_when_nothing_was_removed(self, mock_update_all_cache):
        engine = Engine()
        assert engine._cleanup_failed_round(99) is True
        mock_update_all_cache.assert_not_called()

    @patch("scoring_engine.engine.engine.update_all_cache")
    def test_cache_failure_does_not_break_cleanup(self, mock_update_all_cache):
        mock_update_all_cache.side_effect = RuntimeError("redis is gone")
        env = _make_service()
        round_obj = Round(round_start=datetime.now(), number=4)
        db.session.add(round_obj)
        db.session.commit()
        db.session.add(Check(service=env.service, round=round_obj))
        db.session.commit()

        engine = Engine()
        # The round is still gone, and the cache blow-up did not escape
        assert engine._cleanup_failed_round(4) is True
        assert db.session.query(Round).count() == 0

    @patch("scoring_engine.engine.engine.update_all_cache")
    @patch("scoring_engine.engine.engine.execute_command")
    def test_failed_round_flushes_caches(self, mock_execute_command, mock_update_all_cache, monkeypatch):
        _make_service()
        self._wire_successful_tasks(mock_execute_command)
        self._break_check_commit(monkeypatch)

        engine = Engine(total_rounds=1)
        engine.CLEANUP_RETRY_DELAY = 0
        engine.ROUND_FAILURE_BACKOFF_BASE = 0
        engine.run()

        # The round never finished, so the only flush is the one that follows
        # the rollback of the discarded round.
        assert mock_update_all_cache.call_count == 1


class FakeRedisPipeline:
    """Just enough of a redis-py pipeline for ``RedisBackend._set``."""

    def __init__(self, client):
        self.client = client
        self.commands = []

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def setex(self, key, ttl, value):
        self.commands.append((key, value))
        return self

    def set(self, key, value):
        self.commands.append((key, value))
        return self

    def publish(self, key, value):
        return self

    def execute(self):
        for key, value in self.commands:
            self.client.store[key] = value
        self.commands = []
        return []


class FakeRedisClient:
    """A dict pretending to be a redis connection.

    Only the wire is faked -- every line of Celery's own RedisBackend runs for
    real on top of it.
    """

    def __init__(self):
        self.store = {}
        self.mget_calls = []

    def pipeline(self):
        return FakeRedisPipeline(self)

    def mget(self, keys):
        keys = list(keys)
        self.mget_calls.append(keys)
        return [self.store.get(key) for key in keys]

    def get(self, key):
        return self.store.get(key)


class TestRealResultBackendContract:
    """Pin the Celery contract the batched fast path depends on.

    The other tests here use a hand-written stand-in for the result backend, so
    on their own they would happily keep passing if Celery renamed a method or
    changed how results are stored.  These tests run the real
    ``celery.backends.redis.RedisBackend`` -- real key naming, real serializer,
    real ``mget`` -- with only the redis socket replaced by a dict, so no server
    is needed.
    """

    @pytest.fixture
    def backend(self):
        backend = RedisBackend(app=celery_app)
        client = FakeRedisClient()
        # ``client`` is a cached_property; seeding __dict__ stops it dialling out
        backend.__dict__["client"] = client
        return backend

    def test_configured_backend_is_a_key_value_backend(self):
        """The engine's fast path only exists because the app uses redis."""
        assert isinstance(celery_app.backend, RedisBackend)
        for attribute in ("get_key_for_task", "mget", "decode_result"):
            assert callable(getattr(celery_app.backend, attribute))

    @patch("scoring_engine.engine.engine.execute_command")
    def test_reads_results_the_real_backend_wrote(self, mock_execute_command, backend, db_session):
        mock_execute_command.backend = backend
        job = {"environment_id": 12, "errored_out": False, "output": "pong", "command": "ping -c 1"}
        backend.store_result("done-task", job, states.SUCCESS)

        engine = Engine()
        metas = engine._fetch_task_metas(["done-task", "never-ran"])

        assert metas["done-task"] == {"status": states.SUCCESS, "result": job}
        # A task the backend has never stored looks PENDING, exactly like
        # AsyncResult reports it -- the engine keeps waiting for it.
        assert metas["never-ran"] == {"status": states.PENDING, "result": None}
        assert engine._batch_result_fetch is True
        mock_execute_command.AsyncResult.assert_not_called()

    @patch("scoring_engine.engine.engine.execute_command")
    def test_one_mget_covers_every_task_and_uses_celery_key_names(
        self, mock_execute_command, backend, db_session
    ):
        mock_execute_command.backend = backend
        task_ids = ["task-{0}".format(i) for i in range(5)]
        for task_id in task_ids:
            backend.store_result(task_id, {"environment_id": 1}, states.SUCCESS)

        engine = Engine()
        metas = engine._fetch_task_metas(task_ids)

        client = backend.__dict__["client"]
        assert len(client.mget_calls) == 1
        assert client.mget_calls[0] == [backend.get_key_for_task(task_id) for task_id in task_ids]
        # Celery's own key naming, not ours
        assert client.mget_calls[0][0] in client.store
        assert all(meta["status"] == states.SUCCESS for meta in metas.values())

    @patch("scoring_engine.engine.engine.execute_command")
    def test_failed_tasks_never_yield_a_result_payload(self, mock_execute_command, backend, db_session):
        mock_execute_command.backend = backend
        backend.store_result("boom-task", RuntimeError("boom"), states.FAILURE)

        engine = Engine()
        metas = engine._fetch_task_metas(["boom-task"])

        # The engine treats a missing/non-dict result as a timed out check, so
        # what matters is that a failure never smuggles in a payload.
        assert metas["boom-task"]["status"] == states.FAILURE
        assert metas["boom-task"]["result"] is None

    @patch("scoring_engine.engine.engine.execute_command")
    def test_pending_and_finished_tasks_are_told_apart(self, mock_execute_command, backend, db_session):
        mock_execute_command.backend = backend
        backend.store_result("finished", {"environment_id": 1}, states.SUCCESS)

        engine = Engine()
        completed = set()
        metas = {}
        pending = engine.all_pending_tasks({"Team1": ["finished", "still-going"]}, completed, metas)

        assert pending == ["still-going"]
        assert completed == {"finished"}
        assert metas["finished"]["result"] == {"environment_id": 1}


class TestConsecutiveRoundFailureBound:
    """Tolerating transient failures is right; tolerating them forever is not."""

    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        for name in ("target_round_time", "worker_refresh_time"):
            setting = Setting.get_setting(name)
            setting.value = 0
            db.session.add(setting)
        db.session.commit()

    @staticmethod
    def _wire_successful_tasks(mock_execute_command):
        backend = FakeResultBackend()
        mock_execute_command.backend = backend
        counter = itertools.count()

        def fake_apply_async(args=None, queue=None, countdown=0):
            job = args[0]
            task_id = "task-{0}".format(next(counter))
            backend.store[task_id] = _success_meta(job["environment_id"])
            return MagicMock(id=task_id)

        mock_execute_command.apply_async.side_effect = fake_apply_async
        return backend

    @staticmethod
    def _fail_check_commit_on_rounds(monkeypatch, fail_on=None):
        """Blow up the commit that writes checks, on the given round attempts.

        ``fail_on=None`` fails every round.  Only the check commit is broken, so
        the round cleanup itself still works and the engine keeps looping.
        """
        real_commit = db.session.commit
        state = {"attempts": 0}

        def flaky_commit():
            if any(isinstance(obj, Check) for obj in db.session.new):
                state["attempts"] += 1
                if fail_on is None or state["attempts"] in fail_on:
                    raise RuntimeError("database went away")
            return real_commit()

        monkeypatch.setattr(db.session, "commit", flaky_commit)
        return state

    @staticmethod
    def _record_sleeps(engine):
        sleeps = []
        engine.sleep = sleeps.append
        return sleeps

    @patch("scoring_engine.engine.engine.execute_command")
    def test_engine_exits_when_the_bound_is_hit(self, mock_execute_command, monkeypatch):
        _make_service()
        self._wire_successful_tasks(mock_execute_command)
        self._fail_check_commit_on_rounds(monkeypatch)

        # total_rounds is only a safety net so a broken bound cannot hang here
        engine = Engine(total_rounds=10)
        engine.CLEANUP_RETRY_DELAY = 0
        engine.ROUND_FAILURE_BACKOFF_BASE = 0
        engine.max_consecutive_round_failures = 3

        with pytest.raises(SystemExit) as exit_info:
            engine.run()

        assert exit_info.value.code == 1
        assert engine.consecutive_round_failures == 3
        assert engine.rounds_run == 3
        # Every failed round was still discarded cleanly on the way out
        assert db.session.query(Round).count() == 0
        assert db.session.query(Check).count() == 0
        assert db.session.query(KB).count() == 0

    @patch("scoring_engine.engine.engine.execute_command")
    def test_the_underlying_error_is_logged_before_exiting(self, mock_execute_command, monkeypatch):
        _make_service()
        self._wire_successful_tasks(mock_execute_command)
        self._fail_check_commit_on_rounds(monkeypatch)

        engine = Engine(total_rounds=10)
        engine.CLEANUP_RETRY_DELAY = 0
        engine.ROUND_FAILURE_BACKOFF_BASE = 0
        engine.max_consecutive_round_failures = 2

        with patch("scoring_engine.engine.engine.logger") as mock_logger:
            with pytest.raises(SystemExit):
                engine.run()

        give_up_calls = [
            call for call in mock_logger.error.call_args_list if "consecutive round(s) have failed" in call.args[0]
        ]
        assert len(give_up_calls) == 1
        # The exception that caused the give-up is part of the message
        assert isinstance(give_up_calls[0].args[-1], RuntimeError)
        # ...and the traceback was logged too
        assert mock_logger.exception.called

    @patch("scoring_engine.engine.engine.execute_command")
    def test_counter_resets_on_a_successful_round(self, mock_execute_command, monkeypatch):
        """Failures below the bound recover; the counter must not accumulate."""
        _make_service()
        self._wire_successful_tasks(mock_execute_command)
        # Rounds 1, 2, 4 and 5 fail -- four failures in six rounds, but never
        # three in a row, so the engine must survive all of them.
        self._fail_check_commit_on_rounds(monkeypatch, fail_on={1, 2, 4, 5})

        engine = Engine(total_rounds=6)
        engine.CLEANUP_RETRY_DELAY = 0
        engine.ROUND_FAILURE_BACKOFF_BASE = 0
        engine.max_consecutive_round_failures = 3

        engine.run()

        assert engine.rounds_run == 6
        assert engine.consecutive_round_failures == 0
        # Only the two rounds that finished were recorded
        assert [r.number for r in db.session.query(Round).all()] == [1, 2]
        assert db.session.query(Check).count() == 2

    @patch("scoring_engine.engine.engine.execute_command")
    def test_bound_can_be_disabled(self, mock_execute_command, monkeypatch):
        _make_service()
        self._wire_successful_tasks(mock_execute_command)
        self._fail_check_commit_on_rounds(monkeypatch)

        engine = Engine(total_rounds=4)
        engine.CLEANUP_RETRY_DELAY = 0
        engine.ROUND_FAILURE_BACKOFF_BASE = 0
        engine.max_consecutive_round_failures = 0

        engine.run()

        assert engine.rounds_run == 4
        assert engine.consecutive_round_failures == 4

    def test_bound_comes_from_config(self):
        engine = Engine()
        assert engine.max_consecutive_round_failures == engine.config.max_consecutive_round_failures
        assert engine.consecutive_round_failures == 0

    def test_disabling_the_bound_is_announced_at_startup(self):
        """Opting out of the bound is allowed, but never silently."""
        with patch("scoring_engine.engine.engine.config.max_consecutive_round_failures", 0):
            with patch("scoring_engine.engine.engine.logger") as mock_logger:
                engine = Engine()

        assert engine.max_consecutive_round_failures == 0
        assert any(
            "max_consecutive_round_failures is disabled" in call.args[0]
            for call in mock_logger.warning.call_args_list
        )

    @patch("scoring_engine.engine.engine.execute_command")
    def test_failed_rounds_back_off_before_retrying(self, mock_execute_command, monkeypatch):
        """Retrying instantly would hammer a database that is already sick."""
        _make_service()
        self._wire_successful_tasks(mock_execute_command)
        self._fail_check_commit_on_rounds(monkeypatch)

        engine = Engine(total_rounds=10)
        engine.CLEANUP_RETRY_DELAY = 0
        engine.max_consecutive_round_failures = 3
        sleeps = self._record_sleeps(engine)

        with pytest.raises(SystemExit):
            engine.run()

        # target_round_time is 0 here, so every sleep is the back-off: it grows
        # per consecutive failure, and the third failure exits instead.
        assert sleeps == [
            engine.ROUND_FAILURE_BACKOFF_BASE,
            engine.ROUND_FAILURE_BACKOFF_BASE * 2,
        ]

    def test_backoff_is_capped(self):
        engine = Engine()
        sleeps = self._record_sleeps(engine)

        engine._sleep_after_failed_round(_utcnow(), consecutive_failures=99)

        assert sleeps == [engine.ROUND_FAILURE_BACKOFF_MAX]

    def test_round_pacing_still_wins_when_it_is_longer(self):
        setting = Setting.get_setting("target_round_time")
        setting.value = 120
        db.session.add(setting)
        db.session.commit()
        Setting.clear_cache("target_round_time")

        engine = Engine()
        sleeps = self._record_sleeps(engine)

        engine._sleep_after_failed_round(_utcnow(), consecutive_failures=1)

        assert sleeps == [120]


class TestUtcNow:
    def test_returns_naive_utc(self):
        from datetime import timezone

        now = _utcnow()
        assert now.tzinfo is None  # naive
        # Within a couple seconds of real UTC (not local time).
        delta = abs((datetime.now(timezone.utc).replace(tzinfo=None) - now).total_seconds())
        assert delta < 5


class TestCompetitionWindowGating:
    def test_engine_idles_outside_window(self):
        """With a competition window entirely in the past, the engine must idle
        (sleep pause_duration) instead of running a round."""
        from scoring_engine.models.competition_window import CompetitionWindow
        from scoring_engine.models.round import Round

        db.session.add(
            CompetitionWindow(
                name="past",
                start_time=datetime(2020, 1, 1, 9, 0, 0),
                end_time=datetime(2020, 1, 1, 17, 0, 0),
                enabled=True,
            )
        )
        db.session.commit()

        engine = Engine()
        sleeps = []

        def fake_sleep(seconds):
            sleeps.append(seconds)
            engine.last_round = True  # break the loop after one idle cycle

        engine.sleep = fake_sleep
        engine.run()

        assert sleeps  # it idled at least once
        assert engine.rounds_run == 0
        assert db.session.query(Round).count() == 0

    def test_engine_runs_with_no_windows(self):
        """No windows configured -> engine_should_run is unconditionally True, so
        the loop reaches the round body (which we short-circuit via sleep)."""
        from scoring_engine.engine.engine import engine_should_run

        engine = Engine()
        assert engine_should_run(session=db.session) is True
