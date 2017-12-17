import sys


class MockConfigLoader():
    def __init__(self):
        self.mock_keyname = True


class TestConfig(object):

    def test_config_variable(self):
        if 'scoring_engine.config_loader' in sys.modules:
            del sys.modules['scoring_engine.config_loader']
        import scoring_engine.config_loader

        scoring_engine.config_loader.ConfigLoader = MockConfigLoader

        if 'scoring_engine.config' in sys.modules:
            del sys.modules['scoring_engine.config']
        from scoring_engine.config import config

        assert config.mock_keyname is True
