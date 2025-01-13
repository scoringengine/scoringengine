from shlex import quote

from scoring_engine.engine.basic_check import CHECKS_BIN_PATH

from tests.scoring_engine.checks.check_test import CheckTest


class TestFTPCheck(CheckTest):
    check_name = "FTPCheck"
    properties = {"remotefilepath": "/adir/textfile.txt", "filecontents": "Sample contents"}
    accounts = {"testuser": "testpass"}

    cmd = f"{CHECKS_BIN_PATH}/ftp_check 127.0.0.1 1234 testuser testpass /adir/textfile.txt 'Sample contents'"
