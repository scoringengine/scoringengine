import sys

if 'scoring_engine.config_loader' in sys.modules:
    del sys.modules['scoring_engine.config_loader']
import scoring_engine.config_loader


class MockConfigLoader():
    def __init__(self):
        self.mock_keyname = True

scoring_engine.config_loader.ConfigLoader = MockConfigLoader

del sys.modules['scoring_engine.config']
from scoring_engine.config import config


class TestConfig(object):

    def test_config_variable(self):
        assert config.mock_keyname is True
