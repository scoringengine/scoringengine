from sys import modules
from os import path

from tests.mock_config import MockConfig


def pytest_addoption(parser):
    parser.addoption(
        "--integration",
        action='store_true',
        default=False,
        help="A flag to indicate if integration tests should be executed. This excludes all other type of tests."
    )


collect_ignore = []


def pytest_configure(config):
    # If the integration flag is set, we only
    # load and run tests in the integration directory
    # else, we load our normal tests
    if config.getoption("--integration"):
        collect_ignore[:] = ["scoring_engine"]
        local_config_location = 'integration/engine.conf.inc'
    else:
        collect_ignore[:] = ["integration"]
        local_config_location = 'scoring_engine/engine.conf.inc'
    # This is so that we can override (mock) the config
    # variable, so that we can tell it to load our custom
    # unit test based config file
    config_location = path.join(path.dirname(path.abspath(__file__)), local_config_location)
    modules['scoring_engine.config'] = MockConfig(config_location)
