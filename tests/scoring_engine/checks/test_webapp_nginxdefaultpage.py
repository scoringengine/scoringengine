from tests.scoring_engine.checks.check_test import CheckTest


class TestWebappNginxdefaultpageCheck(CheckTest):
    check_name = "WebappNginxdefaultpageCheck"
    properties = {"scheme": "http", "basepath": "/"}
    cmd = "pytest --tb=line -s -q -rA --scheme=http --hostip=127.0.0.1 --hostport=1234 --basepath=/ /usr/local/scoring_engine/checks/bin/webapp_nginxdefaultpage_check.py"
