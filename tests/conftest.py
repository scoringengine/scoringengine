from os import path
from sys import modules
from scoring_engine.config_loader import ConfigLoader


class MockConfig(object):
    @property
    def config(self):
        file_location = path.join(path.dirname(path.abspath(__file__)), 'scoring_engine/engine.conf')
        return ConfigLoader(file_location)


def pytest_configure(config):
    # This is so that we can override (mock) the config
    # variable, so that we can tell it to load our custom
    # unit test based config file
    modules['scoring_engine.config'] = MockConfig()
