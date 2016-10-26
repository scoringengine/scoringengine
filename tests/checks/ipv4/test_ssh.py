import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../scoring_engine'))

from engine import Engine
from config import Config


class TestSSHCheck(object):

    def setup(self):
      self.config = Config()
      engine = Engine(checks_location=self.config.checks_location)
      self.check_obj = engine.checks[1]('127.0.0.1')

    def test_ssh_check(self):
        self.check_obj.set_credentials(username='test', password='testerson')
        assert self.check_obj.command() == 'ssh command here'
