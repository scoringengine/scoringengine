from scoring_engine.engine.engine import Engine

from scoring_engine.models.setting import Setting

from scoring_engine.checks.agent import AgentCheck
from scoring_engine.checks.icmp import ICMPCheck
from scoring_engine.checks.ssh import SSHCheck
from scoring_engine.checks.dns import DNSCheck
from scoring_engine.checks.ftp import FTPCheck
from scoring_engine.checks.http import HTTPCheck
from scoring_engine.checks.https import HTTPSCheck
from scoring_engine.checks.mysql import MYSQLCheck
from scoring_engine.checks.mssql import MSSQLCheck
from scoring_engine.checks.postgresql import POSTGRESQLCheck
from scoring_engine.checks.pop3 import POP3Check
from scoring_engine.checks.pop3s import POP3SCheck
from scoring_engine.checks.imap import IMAPCheck
from scoring_engine.checks.imaps import IMAPSCheck
from scoring_engine.checks.smtp import SMTPCheck
from scoring_engine.checks.smb import SMBCheck
from scoring_engine.checks.smtps import SMTPSCheck
from scoring_engine.checks.vnc import VNCCheck
from scoring_engine.checks.elasticsearch import ElasticsearchCheck
from scoring_engine.checks.ldap import LDAPCheck
from scoring_engine.checks.rdp import RDPCheck
from scoring_engine.checks.wordpress import WordpressCheck
from scoring_engine.checks.nfs import NFSCheck
from scoring_engine.checks.openvpn import OpenVPNCheck
from scoring_engine.checks.telnet import TelnetCheck
from scoring_engine.checks.winrm import WinRMCheck

from tests.scoring_engine.unit_test import UnitTest


class TestEngine(UnitTest):
    def setup(self):
        super(TestEngine, self).setup()
        target_round_time_obj = Setting.get_setting("target_round_time")
        target_round_time_obj.value = 0
        self.session.add(target_round_time_obj)
        worker_refresh_time_obj = Setting.get_setting("worker_refresh_time")
        worker_refresh_time_obj.value = 0
        self.session.add(worker_refresh_time_obj)

        self.session.commit()

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

    # todo figure out how to test the remaining functionality of engine
    # where we're waiting for the worker queues to finish and everything
