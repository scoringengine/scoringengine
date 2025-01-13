from scoring_engine.engine.basic_check import CHECKS_BIN_PATH

from tests.scoring_engine.checks.check_test import CheckTest


class TestSMBCheck(CheckTest):
    check_name = "SMBCheck"
    properties = {"remote_name": "COMPUTERNAME", "share": "ScoringShare", "file": "flag.txt", "hash": "123456789"}
    accounts = {"pwnbus": "pwnbuspass"}
    cmd = (
        CHECKS_BIN_PATH
        + "/smb_check --host 127.0.0.1 --port 1234 --user pwnbus --pass pwnbuspass --remote-name COMPUTERNAME --share ScoringShare --file flag.txt --hash 123456789"
    )
