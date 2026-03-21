from os import environ, path
from sys import modules

import pytest

from tests.mock_config import MockConfig


def pytest_addoption(parser):
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="A flag to indicate if integration tests should be executed. This excludes all other type of tests.",
    )


collect_ignore = []


def pytest_configure(config):
    # If the integration flag is set, we only
    # load and run tests in the integration directory
    # else, we load our normal tests
    if config.getoption("--integration"):
        collect_ignore[:] = ["scoring_engine"]
        local_config_location = "integration/engine.conf.inc"
    else:
        collect_ignore[:] = ["integration"]
        local_config_location = "scoring_engine/engine.conf.inc"

    # When running under pytest-xdist, each worker gets a unique DB file
    # so they don't stomp on each other's SQLite databases.
    worker_id = environ.get("PYTEST_XDIST_WORKER")
    if worker_id is not None:
        environ["SCORINGENGINE_DB_URI"] = f"sqlite:////tmp/test_engine_{worker_id}.db?check_same_thread=False"

    # This is so that we can override (mock) the config
    # variable, so that we can tell it to load our custom
    # unit test based config file
    config_location = path.join(path.dirname(path.abspath(__file__)), local_config_location)
    modules["scoring_engine.config"] = MockConfig(config_location)


@pytest.fixture(scope="session")
def app_context():
    """
    Create a Flask application context for tests that need it.
    This is required for Flask-SQLAlchemy to work properly.
    Used by integration tests via their conftest fixture.
    UnitTest-based tests create their own context in setup_method.
    """
    from scoring_engine.web import create_app

    app = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        yield app
