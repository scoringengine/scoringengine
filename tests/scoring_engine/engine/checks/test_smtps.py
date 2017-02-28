from tests.scoring_engine.engine.checks.check_test import CheckTest


class TestSMTPSCheck(CheckTest):
    check_name = 'SMTPSCheck'
    properties = {
        'domain': 'test.com',
    }
    accounts = {
        'testuser': 'passtest'
    }
    cmd = "medusa -s -R 1 -h '127.0.0.1' -n 100 -u 'testuser@test.com' -p 'passtest' -M smtp"
