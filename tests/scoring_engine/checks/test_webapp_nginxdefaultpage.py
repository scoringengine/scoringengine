from scoring_engine.engine.basic_check import CHECKS_BIN_PATH

from tests.scoring_engine.checks.check_test import CheckTest


class TestWebappNginxdefaultpageCheck(CheckTest):
    check_name = "WebappNginxdefaultpageCheck"
    properties = {"scheme": "http", "basepath": "/"}
    cmd = f"pytest --tb=line -s -q -rA --scheme=http --hostip=127.0.0.1 --hostport=1234 --basepath=/ {CHECKS_BIN_PATH}/webapp_nginxdefaultpage_check.py"
