from scoring_engine.engine.basic_check import CHECKS_BIN_PATH

from tests.scoring_engine.checks.check_test import CheckTest


class TestSSHCheck(CheckTest):
    check_name = "SSHCheck"
    properties = {"commands": "ls -l;id"}
    accounts = {"pwnbus": "pwnbuspass"}
    cmd = CHECKS_BIN_PATH + "/ssh_check 127.0.0.1 1234 pwnbus pwnbuspass 'ls -l;id'"
