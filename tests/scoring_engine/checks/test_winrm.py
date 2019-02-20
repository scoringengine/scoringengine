from scoring_engine.engine.basic_check import CHECKS_BIN_PATH

from tests.scoring_engine.checks.check_test import CheckTest


class TestSSHCheck(CheckTest):
    check_name = 'winrmCheck'
    properties = {
        'commands': 'echo CHECKINFLAG'
    }
    accounts = {
        'test': 'testpass'
    }
    cmd = CHECKS_BIN_PATH + "/winrm_check '127.0.0.1' 5985 'test' 'testpass' 'echo CHECKINFLAG'"
