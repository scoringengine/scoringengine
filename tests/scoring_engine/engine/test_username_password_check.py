import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.engine.username_password_check import UsernamePasswordCheck


class TestBasicCheck(object):

    def setup(self):
        self.check = UsernamePasswordCheck("127.0.0.1")

    def test_init(self):
        assert self.check.host_address == "127.0.0.1"

    def test_with_creds(self):
        self.check.set_credentials('testuser', 'testpass')
        assert self.check.username == 'testuser'
        assert self.check.password == 'testpass'
