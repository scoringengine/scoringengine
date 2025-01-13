from tests.scoring_engine.checks.check_test import CheckTest


class TestICMPCheck(CheckTest):
    check_name = "ICMPCheck"
    cmd = "ping -c 1 127.0.0.1"
