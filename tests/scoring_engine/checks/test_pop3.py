from tests.scoring_engine.checks.check_test import CheckTest


class TestPOP3Check(CheckTest):
    check_name = "POP3Check"
    properties = {
        "domain": "test.com",
    }
    accounts = {"testuser": "passtest"}
    cmd = "medusa -R 1 -h 127.0.0.1 -n 1234 -u testuser@test.com -p passtest -M pop3"
