import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.engine.engine import Engine


class TestSSHCheck(object):

    def setup(self):
      engine = Engine()
      self.check_obj = engine.checks[1]('127.0.0.1')

    def test_ssh_check(self):
        self.check_obj.set_credentials(username='test', password='testerson')
        assert self.check_obj.command() == 'ssh command here'
