from scoring_engine.engine.basic_check import CHECKS_BIN_PATH

from tests.scoring_engine.checks.check_test import CheckTest


class TestWinRMCheck(CheckTest):
    check_name = "WinRMCheck"
    properties = {"commands": "dir"}

    accounts = {"pwnbus": "pwnbuspass"}
    cmd = CHECKS_BIN_PATH + "/winrm_check 127.0.0.1 pwnbus pwnbuspass dir"
