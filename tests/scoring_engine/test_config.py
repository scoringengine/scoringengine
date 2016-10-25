import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../scoring_engine'))

from config import Config


class TestConfig(object):

    def setup(self):
        self.config = Config()

    def test_checks_location(self):
        assert self.config.checks_location == "checks"

    def test_db_host(self):
        assert self.config.db_host == "127.0.0.1"

    def test_db_port(self):
        assert self.config.db_port == "3306"

    def test_db_username(self):
        assert self.config.db_username == "testuser"

    def test_db_password(self):
        assert self.config.db_password == "testpass"
