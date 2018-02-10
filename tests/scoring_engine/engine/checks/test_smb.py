from scoring_engine.engine.basic_check import CHECKS_BIN_PATH

from tests.scoring_engine.engine.checks.check_test import CheckTest


class TestSMBCheck(CheckTest):
    check_name = 'SMBCheck'
    required_properties = ['share', 'file', 'hash']
    properties = {
        'share': 'ScoringShare',
        'file': 'flag.txt',
        'hash': '123456789'
    }
    accounts = {
        'pwnbus': 'pwnbuspass'
    }
    cmd = CHECKS_BIN_PATH + "/smb_check --host '127.0.0.1' --port 100 --user 'pwnbus' --pass 'pwnbuspass' --share 'ScoringShare' --file 'flag.txt' --hash '123456789'"
