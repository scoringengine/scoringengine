from scoring_engine.engine.engine import Engine

from tests.scoring_engine.unit_test import UnitTest


class TestEngine(UnitTest):

    def test_init(self):
        engine = Engine()
        from scoring_engine.engine.checks.icmp import ICMPCheck
        from scoring_engine.engine.checks.ssh import SSHCheck
        from scoring_engine.engine.checks.dns import DNSCheck
        from scoring_engine.engine.checks.ftpdownload import FTPDownloadCheck
        from scoring_engine.engine.checks.ftpupload import FTPUploadCheck
        from scoring_engine.engine.checks.http import HTTPCheck
        from scoring_engine.engine.checks.https import HTTPSCheck
        from scoring_engine.engine.checks.mysql import MYSQLCheck
        from scoring_engine.engine.checks.postgresql import POSTGRESQLCheck
        from scoring_engine.engine.checks.pop3 import POP3Check
        from scoring_engine.engine.checks.imap import IMAPCheck
        from scoring_engine.engine.checks.smtp import SMTPCheck
        expected_checks = [
            ICMPCheck,
            SSHCheck,
            DNSCheck,
            FTPDownloadCheck,
            FTPUploadCheck,
            HTTPCheck,
            HTTPSCheck,
            MYSQLCheck,
            POSTGRESQLCheck,
            POP3Check,
            IMAPCheck,
            SMTPCheck,
        ]
        assert set(engine.checks) == set(expected_checks)

    def test_total_rounds_init(self):
        engine = Engine(total_rounds=100)
        assert engine.total_rounds == 100

    def test_custom_sleep_timers(self):
        engine = Engine(round_time_sleep=60, worker_wait_time=20)
        assert engine.round_time_sleep == 60
        assert engine.worker_wait_time == 20

    def test_shutdown(self):
        engine = Engine()
        assert engine.last_round is False
        engine.shutdown()
        assert engine.last_round is True

    def test_run_one_round(self):
        engine = Engine(total_rounds=1, round_time_sleep=1, worker_wait_time=1)
        assert engine.rounds_run == 0
        engine.run()
        assert engine.rounds_run == 1
        assert engine.current_round == 1

    def test_run_ten_rounds(self):
        engine = Engine(total_rounds=10, round_time_sleep=0, worker_wait_time=0)
        assert engine.current_round == 0
        assert engine.rounds_run == 0
        engine.run()
        assert engine.rounds_run == 10
        assert engine.current_round == 10

    def test_run_hundred_rounds(self):
        engine = Engine(total_rounds=100, round_time_sleep=0, worker_wait_time=0)
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
