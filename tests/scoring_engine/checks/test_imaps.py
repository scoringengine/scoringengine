from tests.scoring_engine.checks.check_test import CheckTest


class TestIMAPSCheck(CheckTest):
    check_name = "IMAPSCheck"
    properties = {
        "domain": "test.com",
    }
    accounts = {"testuser": "passtest"}
    cmd = "medusa -s -R 1 -h 127.0.0.1 -n 1234 -u testuser@test.com -p passtest -M imap -m AUTH:LOGIN"
