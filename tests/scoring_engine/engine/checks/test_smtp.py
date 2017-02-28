from tests.scoring_engine.engine.checks.check_test import CheckTest


class TestSMTPCheck(CheckTest):
    check_name = 'SMTPCheck'
    properties = {
        'domain': 'test.com',
    }
    accounts = {
        'testuser': 'passtest'
    }
    cmd = "medusa -R 1 -h '127.0.0.1' -n 100 -u 'testuser@test.com' -p 'passtest' -M smtp"
