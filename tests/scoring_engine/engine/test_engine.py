from unittest.mock import MagicMock, patch

import pytest

from scoring_engine.checks.agent import AgentCheck
from scoring_engine.checks.dns import DNSCheck
from scoring_engine.checks.elasticsearch import ElasticsearchCheck
from scoring_engine.checks.ftp import FTPCheck
from scoring_engine.checks.http import HTTPCheck
from scoring_engine.checks.https import HTTPSCheck
from scoring_engine.checks.icmp import ICMPCheck
from scoring_engine.checks.imap import IMAPCheck
from scoring_engine.checks.imaps import IMAPSCheck
from scoring_engine.checks.ldap import LDAPCheck
from scoring_engine.checks.mssql import MSSQLCheck
from scoring_engine.checks.mysql import MYSQLCheck
from scoring_engine.checks.nfs import NFSCheck
from scoring_engine.checks.openvpn import OpenVPNCheck
from scoring_engine.checks.pop3 import POP3Check
from scoring_engine.checks.pop3s import POP3SCheck
from scoring_engine.checks.postgresql import POSTGRESQLCheck
from scoring_engine.checks.rdp import RDPCheck
from scoring_engine.checks.smb import SMBCheck
from scoring_engine.checks.smtp import SMTPCheck
from scoring_engine.checks.smtps import SMTPSCheck
from scoring_engine.checks.ssh import SSHCheck
from scoring_engine.checks.telnet import TelnetCheck
from scoring_engine.checks.vnc import VNCCheck
from scoring_engine.checks.webapp_nginxdefaultpage import WebappNginxdefaultpageCheck
from scoring_engine.checks.webapp_scoringengine import WebappScoringengineCheck
from scoring_engine.checks.winrm import WinRMCheck
from scoring_engine.checks.wordpress import WordpressCheck
from scoring_engine.db import db
from scoring_engine.engine.engine import Engine
from scoring_engine.models.environment import Environment
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
        engine = Engine()
        expected_checks = [
            AgentCheck,
            ICMPCheck,
            SSHCheck,
            DNSCheck,
            FTPCheck,
            HTTPCheck,
            HTTPSCheck,
            MYSQLCheck,
            MSSQLCheck,
            POSTGRESQLCheck,
            POP3Check,
            POP3SCheck,
            IMAPCheck,
            IMAPSCheck,
            SMTPCheck,
            SMTPSCheck,
            VNCCheck,
            ElasticsearchCheck,
            LDAPCheck,
            SMBCheck,
            RDPCheck,
            WordpressCheck,
            NFSCheck,
            OpenVPNCheck,
            WebappScoringengineCheck,
            WebappNginxdefaultpageCheck,
            TelnetCheck,
            WinRMCheck,
        ]
        assert {cls.__name__ for cls in engine.checks} == {
            cls.__name__ for cls in expected_checks
        }, "Mismatch in check names"

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
        check_obj = engine.check_name_to_obj("ICMP IPv4 Check")
        from scoring_engine.checks.icmp import ICMPCheck

        check_obj == ICMPCheck

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

    # todo figure out how to test the remaining functionality of engine
    # where we're waiting for the worker queues to finish and everything
