from scoring_engine.engine.engine import Engine

from scoring_engine.models.setting import Setting

from scoring_engine.engine.checks.icmp import ICMPCheck
from scoring_engine.engine.checks.ssh import SSHCheck
from scoring_engine.engine.checks.dns import DNSCheck
from scoring_engine.engine.checks.ftp import FTPCheck
from scoring_engine.engine.checks.http import HTTPCheck
from scoring_engine.engine.checks.https import HTTPSCheck
from scoring_engine.engine.checks.mysql import MYSQLCheck
from scoring_engine.engine.checks.postgresql import POSTGRESQLCheck
from scoring_engine.engine.checks.pop3 import POP3Check
from scoring_engine.engine.checks.pop3s import POP3SCheck
from scoring_engine.engine.checks.imap import IMAPCheck
from scoring_engine.engine.checks.imaps import IMAPSCheck
from scoring_engine.engine.checks.smtp import SMTPCheck
from scoring_engine.engine.checks.smtps import SMTPSCheck
from scoring_engine.engine.checks.vnc import VNCCheck

from tests.scoring_engine.unit_test import UnitTest


class TestEngine(UnitTest):

    def setup(self):
        super(TestEngine, self).setup()
        round_time_sleep_obj = Setting.get_setting('round_time_sleep')
        round_time_sleep_obj.value = 0
        self.session.add(round_time_sleep_obj)
        worker_refresh_time_obj = Setting.get_setting('worker_refresh_time')
        worker_refresh_time_obj.value = 0
        self.session.add(worker_refresh_time_obj)

        self.session.commit()

    def test_init(self):
        engine = Engine()
        expected_checks = [
            ICMPCheck,
            SSHCheck,
            DNSCheck,
            FTPCheck,
            HTTPCheck,
            HTTPSCheck,
            MYSQLCheck,
            POSTGRESQLCheck,
            POP3Check,
            POP3SCheck,
            IMAPCheck,
            IMAPSCheck,
            SMTPCheck,
            SMTPSCheck,
            VNCCheck,
        ]
        assert set(engine.checks) == set(expected_checks)

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
        from scoring_engine.engine.checks.icmp import ICMPCheck
        check_obj == ICMPCheck

    def test_check_name_to_obj_negative(self):
        engine = Engine()
        check_obj = engine.check_name_to_obj("Garbage Check")
        assert check_obj is None

    # todo figure out how to test the remaining functionality of engine
    # where we're waiting for the worker queues to finish and everything
