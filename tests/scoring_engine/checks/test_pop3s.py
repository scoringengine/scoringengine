from tests.scoring_engine.checks.check_test import CheckTest


class TestPOP3SCheck(CheckTest):
    check_name = "POP3SCheck"
    properties = {
        "domain": "test.com",
    }
    accounts = {"testuser": "passtest"}
    cmd = "medusa -s -R 1 -h 127.0.0.1 -n 1234 -u testuser@test.com -p passtest -M pop3"
