from scoring_engine.engine.basic_check import CHECKS_BIN_PATH

from tests.scoring_engine.checks.check_test import CheckTest


class TestWebappScoringengineCheck(CheckTest):
    check_name = "WebappScoringengineCheck"
    properties = {"scheme": "https", "basepath": "/"}
    accounts = {"testuser": "testpass"}
    cmd = f"pytest --tb=line -s -q -rA --scheme=https --hostip=127.0.0.1 --hostport=1234 --basepath=/ --username=testuser --password=testpass {CHECKS_BIN_PATH}/webapp_scoringengine_check.py"
