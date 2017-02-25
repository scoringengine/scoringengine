from tests.scoring_engine.engine.checks.check_test import CheckTest


class TestSSHCheck(CheckTest):
    check_name = 'SSHCheck'
    properties = {
        'command': 'ls -l'
    }
    accounts = {
        'pwnbus': 'pwnbuspass'
    }
    cmd = 'expect -c "spawn ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pwnbus@127.0.0.1 "ls -l"; expect "assword"; send "pwnbuspass\r"; interact"'
