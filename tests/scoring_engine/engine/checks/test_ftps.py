from tests.scoring_engine.engine.checks.check_test import CheckTest


class TestFTPSCheck(CheckTest):
    check_name = 'FTPSCheck'
    accounts = {
        'testuser': 'testpass'
    }
    cmd = "medusa -s -R 1 -h '127.0.0.1' -n 100 -u 'testuser' -p 'testpass' -M ftp"
