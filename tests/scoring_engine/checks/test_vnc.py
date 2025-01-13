from tests.scoring_engine.checks.check_test import CheckTest


class TestVNCCheck(CheckTest):
    check_name = "VNCCheck"
    accounts = {"BLANK": "passtest"}
    cmd = "medusa -R 1 -h 127.0.0.1 -n 1234 -u '' '' -p passtest -M vnc"
