import os

from scoring_engine.config import config


def get_version():
    version = "1.0.0"
    if "SCORINGENGINE_VERSION" in os.environ:
        version = os.environ["SCORINGENGINE_VERSION"]
    if config.debug:
        version += "-dev"
    return version


version = get_version()
