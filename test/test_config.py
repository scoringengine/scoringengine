import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../scoring_engine'))

from config import Config


class TestConfig(object):

    def test_load_config(self):
        config = Config()
        assert config.checks_location == "checks"
