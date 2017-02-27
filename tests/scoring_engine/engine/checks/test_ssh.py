from tests.scoring_engine.engine.checks.check_test import CheckTest


class TestSSHCheck(CheckTest):
    check_name = 'SSHCheck'
    properties = {
        'command': 'ls -l'
    }
    accounts = {
        'pwnbus': 'pwnbuspass'
    }
    cmd = '/usr/bin/ssh_login 127.0.0.1 pwnbus pwnbuspass "ls -l"'
