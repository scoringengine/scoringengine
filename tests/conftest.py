from os import path
from sys import modules
from scoring_engine.config_loader import ConfigLoader


class MockConfig(object):
    @property
    def config(self):
        file_location = path.join(path.dirname(path.abspath(__file__)), 'scoring_engine/example.conf')
        return ConfigLoader(file_location)


def pytest_configure(config):
    modules['scoring_engine.config'] = MockConfig()
