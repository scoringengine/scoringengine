from tests.scoring_engine.engine.checks.check_test import CheckTest


class TestFTPCheck(CheckTest):
    check_name = 'FTPCheck'
    accounts = {
        'testuser': 'testpass'
    }
    cmd = "medusa -R 1 -h '127.0.0.1' -n 100 -u 'testuser' -p 'testpass' -M ftp"
