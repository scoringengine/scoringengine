from tests.scoring_engine.checks.check_test import CheckTest


class TestSMTPSCheck(CheckTest):
    check_name = 'SMTPSCheck'
    properties = {
        'fromuser': 'fromusr@domain.com',
        'touser': 'tousr@someone.com',
        'subject': 'A scoring engine test subject!',
        'body': 'Hello!, This is an email body'
    }
    accounts = {
        'testuser@emaildomain.com': 'passtest'
    }
    cmd = "smtps_check 'testuser@emaildomain.com' 'passtest' 'fromusr@domain.com' 'tousr@someone.com' 'A scoring engine test subject!' 'Hello!, This is an email body' '127.0.0.1' 1234"
