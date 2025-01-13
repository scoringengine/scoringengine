from scoring_engine.engine.basic_check import CHECKS_BIN_PATH

from tests.scoring_engine.checks.check_test import CheckTest


class TestRDPCheck(CheckTest):
    check_name = "RDPCheck"
    accounts = {"pwnbus": "pwnbuspass"}
    cmd = CHECKS_BIN_PATH + "/rdp_check pwnbus pwnbuspass 127.0.0.1 1234"
