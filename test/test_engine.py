import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../scoring_engine'))

from engine import Engine
from config import Config


class TestEngine():

    def setup(self):
        self.config = Config()

    def test_load_checks(self):
        engine = Engine(checks_location=self.config.checks_location)
        loaded_checks = engine.load_checks()
        from ipv4.ssh import SSHCheck
        from ipv4.icmp import ICMPCheck
        expected_checks = [ICMPCheck, SSHCheck]
        assert loaded_checks == expected_checks

    def test_current_round_init(self):
        engine = Engine(checks_location=self.config.checks_location, current_round=100)
        assert engine.current_round == 100

    def test_total_rounds_init(self):
        engine = Engine(checks_location=self.config.checks_location, total_rounds=100)
        assert engine.total_rounds == 100
