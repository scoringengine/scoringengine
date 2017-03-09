from tests.scoring_engine.engine.checks.check_test import CheckTest


class TestSSHCheck(CheckTest):
    check_name = 'SSHCheck'
    properties = {
        'command': 'ls -l'
    }
    accounts = {
        'pwnbus': 'pwnbuspass'
    }
    cmd = "sshpass -p 'pwnbuspass' ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no 'pwnbus@127.0.0.1' -p 100 'ls -l'"
