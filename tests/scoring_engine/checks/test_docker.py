from scoring_engine.engine.basic_check import CHECKS_BIN_PATH

from tests.scoring_engine.checks.check_test import CheckTest


class TestDockerAPICheck(CheckTest):
    check_name = 'DockerAPICheck'
    properties = {
        'docker_image': "hello-world:latest"
    }
    cmd = CHECKS_BIN_PATH + "/docker_check '127.0.0.1' 1234 'hello-world:latest'"
