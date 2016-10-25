import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../scoring_engine'))

from engine import Engine
from config import Config


class TestICMPCheck(object):

    def setup(self):
      self.config = Config()

    def test_ssh_check(self):
        engine = Engine(checks_location=self.config.checks_location)
        checks = engine.load_checks()
        ssh_check_obj = checks[0]('127.0.0.1')
        assert ssh_check_obj.command() == 'ping -c 1 127.0.0.1'
