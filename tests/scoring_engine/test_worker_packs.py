import os
import re
from unittest.mock import MagicMock, patch

import mock
import pytest
import yaml

from scoring_engine.celery_stats import CeleryStats
from scoring_engine.config import config
from scoring_engine.db import db
from scoring_engine.engine.engine import Engine
from scoring_engine.models.environment import Environment
from scoring_engine.models.property import Property
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.worker_packs import (
    PACKS,
    check_pack,
    pack_by_check_name,
    parse_packs,
    queue_for,
    queue_for_service,
    worker_queues,
)

REPO = os.path.join(os.path.dirname(__file__), "..", "..")


class TestPackRouting:
    def test_core_uses_base_queue(self):
        assert queue_for("main", "core") == "main"

    def test_other_packs_get_suffixed_queue(self):
        assert queue_for("main", "browser") == "main.browser"
        assert queue_for("team5", "db") == "team5.db"

    def test_worker_queues(self):
        assert worker_queues("main", ["core", "db"]) == ["main", "main.db"]

    def test_parse_packs(self):
        assert parse_packs(" core, browser ") == ["core", "browser"]

    def test_parse_packs_rejects_unknown(self):
        with pytest.raises(ValueError, match="gpu"):
            parse_packs("core,gpu")

    def test_every_check_declares_a_known_pack(self):
        for check in Engine.load_check_files(config.checks_location):
            assert check_pack(check) in PACKS, check.__name__

    def test_heavy_checks_are_not_in_core(self):
        packs = pack_by_check_name()
        assert packs["WebappScoringengineCheck"] == "browser"
        assert packs["WebappNginxdefaultpageCheck"] == "browser"
        assert packs["RDPCheck"] == "rdp"
        assert {packs["MYSQLCheck"], packs["POSTGRESQLCheck"], packs["MSSQLCheck"]} == {"db"}
        assert packs["SSHCheck"] == "core"


def _service(check_name, props=None, worker_queue="main"):
    team = Team(name="Blue Team 1", color="Blue")
    service = Service(name=check_name, team=team, check_name=check_name, host="127.0.0.1", port=80)
    service.worker_queue = worker_queue
    env = Environment(service=service, matching_content="*")
    db.session.add_all([team, service, env])
    for name, value in (props or {}).items():
        db.session.add(Property(environment=env, name=name, value=value))
    db.session.commit()
    return service, env


class TestEngineDispatch:
    @patch("scoring_engine.engine.engine.execute_command")
    def test_browser_check_dispatched_to_browser_queue(self, mock_execute_command):
        _, env = _service("WebappNginxdefaultpageCheck", {"scheme": "http", "basepath": "/"})
        result = MagicMock(id="t1", state="SUCCESS")
        result.result = {"environment_id": env.id, "errored_out": False, "output": "*", "command": "x"}
        mock_execute_command.apply_async.return_value = result
        mock_execute_command.AsyncResult.return_value = result

        Engine(total_rounds=1).run()

        assert mock_execute_command.apply_async.call_args.kwargs["queue"] == "main.browser"

    def test_queue_for_service(self):
        service, _ = _service("RDPCheck", worker_queue="dmz")
        assert queue_for_service(service) == "dmz.rdp"


class _Control:
    def __init__(self, queues):
        self._queues = queues

    def inspect(self):
        inspect = MagicMock()
        inspect.active_queues.return_value = self._queues
        return inspect


class TestQueueStatsShowsUncoveredPacks:
    def test_pack_queue_without_worker_has_no_workers(self):
        _service("WebappNginxdefaultpageCheck", {"scheme": "http", "basepath": "/"})
        app = mock.Mock()
        app.control = _Control({"core-worker@host": [{"name": "main"}]})
        with mock.patch("scoring_engine.celery_stats.celery_app", app):
            stats = {q["name"]: q for q in CeleryStats.get_queue_stats()}
        assert stats["main.browser"]["workers"] == []


class TestImagesMatchPacks:
    def _dockerfile(self):
        with open(os.path.join(REPO, "docker", "worker", "Dockerfile")) as f:
            return f.read()

    def test_each_target_advertises_its_packs(self):
        dockerfile = self._dockerfile()
        expected = {
            "core": "core",
            "db": "core,db",
            "rdp": "core,rdp",
            "browser": "core,browser",
            "full": "core,db,rdp,browser",
        }
        for target, packs in expected.items():
            stage = dockerfile.split("AS {0}\n".format(target), 1)[1].split("\nFROM ", 1)[0]
            assert "ENV SCORINGENGINE_WORKER_PACKS={0}\n".format(packs) in stage, target
            parse_packs(packs)

    def test_full_is_the_default_target(self):
        stages = re.findall(r"^FROM .* AS (\S+)$", self._dockerfile(), re.M)
        assert stages[-1] == "full"

    def test_compose_has_an_opt_in_worker_per_pack(self):
        with open(os.path.join(REPO, "docker-compose.yml")) as f:
            services = yaml.safe_load(f)["services"]
        assert services["worker"]["build"]["target"] == "${WORKER_TARGET:-full}"
        for pack in ("db", "rdp", "browser"):
            svc = services["worker-{0}".format(pack)]
            assert svc["build"]["target"] == pack
            assert svc["profiles"] == [pack]
