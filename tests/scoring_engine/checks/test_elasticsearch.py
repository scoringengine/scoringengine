from scoring_engine.engine.basic_check import CHECKS_BIN_PATH

from tests.scoring_engine.checks.check_test import CheckTest


class TestElasticsearchCheck(CheckTest):
    check_name = "ElasticsearchCheck"
    properties = {"index": "events", "doc_type": "message"}
    cmd = CHECKS_BIN_PATH + "/elasticsearch_check 127.0.0.1 1234 events message"
