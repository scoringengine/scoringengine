from scoring_engine.engine.basic_check import CHECKS_BIN_PATH

from tests.scoring_engine.checks.check_test import CheckTest


class TestAgentCheck(CheckTest):
    check_name = "AgentCheck"
    # properties = {"qtype": "A", "domain": "www.google.com"}
    cmd = CHECKS_BIN_PATH + "/agent_check 127.0.0.1"
