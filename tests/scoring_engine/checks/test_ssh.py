from scoring_engine.engine.basic_check import CHECKS_BIN_PATH

from tests.scoring_engine.checks.check_test import CheckTest


class TestSSHCheck(CheckTest):
    check_name = "SSHCheck"
    properties = {"commands": "ls -l;id"}
    accounts = {"pwnbus": "pwnbuspass"}
    cmd = CHECKS_BIN_PATH + "/ssh_check 127.0.0.1 1234 pwnbus 'ls -l;id'"
    cmd_env = {"SCORING_PASSWORD": "pwnbuspass"}


class TestSSHCheckWithSingleQuotePassword(CheckTest):
    check_name = "SSHCheck"
    properties = {"commands": "whoami"}
    accounts = {"admin": "pass'word"}
    cmd = CHECKS_BIN_PATH + "/ssh_check 127.0.0.1 1234 admin whoami"
    cmd_env = {"SCORING_PASSWORD": "pass'word"}


class TestSSHCheckWithDoubleQuotePassword(CheckTest):
    check_name = "SSHCheck"
    properties = {"commands": "id"}
    accounts = {"admin": 'pass"word'}
    cmd = CHECKS_BIN_PATH + "/ssh_check 127.0.0.1 1234 admin id"
    cmd_env = {"SCORING_PASSWORD": 'pass"word'}


class TestSSHCheckWithBackslashPassword(CheckTest):
    check_name = "SSHCheck"
    properties = {"commands": "ls"}
    accounts = {"admin": "pass\\word"}
    cmd = CHECKS_BIN_PATH + "/ssh_check 127.0.0.1 1234 admin ls"
    cmd_env = {"SCORING_PASSWORD": "pass\\word"}


class TestSSHCheckWithSpacesInPassword(CheckTest):
    check_name = "SSHCheck"
    properties = {"commands": "pwd"}
    accounts = {"admin": "my secure password"}
    cmd = CHECKS_BIN_PATH + "/ssh_check 127.0.0.1 1234 admin pwd"
    cmd_env = {"SCORING_PASSWORD": "my secure password"}


class TestSSHCheckWithSpecialCharsPassword(CheckTest):
    check_name = "SSHCheck"
    properties = {"commands": "echo test"}
    accounts = {"admin": "p@ss$word!&|;"}
    cmd = CHECKS_BIN_PATH + "/ssh_check 127.0.0.1 1234 admin 'echo test'"
    cmd_env = {"SCORING_PASSWORD": "p@ss$word!&|;"}


class TestSSHCheckWithSpecialCharsUsername(CheckTest):
    check_name = "SSHCheck"
    properties = {"commands": "id"}
    accounts = {"user@domain.com": "password123"}
    cmd = CHECKS_BIN_PATH + "/ssh_check 127.0.0.1 1234 user@domain.com id"
    cmd_env = {"SCORING_PASSWORD": "password123"}
