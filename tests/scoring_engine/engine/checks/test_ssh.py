from tests.scoring_engine.engine.checks.check_test import CheckTest


class TestSSHCheck(CheckTest):
    check_name = 'SSHCheck'
    cmd = 'ssh command here'
