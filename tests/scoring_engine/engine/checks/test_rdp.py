from tests.scoring_engine.engine.checks.check_test import CheckTest


class TestRDPCheck(CheckTest):
    check_name = 'RDPCheck'
    accounts = {
        'pwnbus': 'pwnbuspass'
    }
    cmd = "xfreerdp --ignore-certificate --authonly -u 'pwnbus' -p 'pwnbuspass' '127.0.0.1':1234"
