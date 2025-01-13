from scoring_engine.engine.basic_check import CHECKS_BIN_PATH

from tests.scoring_engine.checks.check_test import CheckTest


class TestTelnetCheck(CheckTest):
    check_name = "TelnetCheck"
    properties = {"timeout": 15, "commands": "ls -l;id"}
    accounts = {"pwnbus": "pwnbuspass"}
    cmd = CHECKS_BIN_PATH + "/telnet_check 127.0.0.1 1234 15 pwnbus pwnbuspass 'ls -l;id'"
