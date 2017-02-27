from tests.scoring_engine.engine.checks.check_test import CheckTest


class TestVNCCheck(CheckTest):
    check_name = 'VNCCheck'
    accounts = {
        'BLANK': 'passtest'
    }
    cmd = "medusa -R 1 -h 127.0.0.1 -u ' ' -p 'passtest' -M vnc"
