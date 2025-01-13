from scoring_engine.engine.basic_check import CHECKS_BIN_PATH

from tests.scoring_engine.checks.check_test import CheckTest


class TestNFSCheck(CheckTest):
    check_name = "NFSCheck"
    properties = {"remotefilepath": "/adir/textfile.txt", "filecontents": "Sample contents"}

    cmd = CHECKS_BIN_PATH + "/nfs_check 127.0.0.1 /adir/textfile.txt 'Sample contents'"
