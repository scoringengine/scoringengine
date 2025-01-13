from scoring_engine.engine.basic_check import CHECKS_BIN_PATH

from tests.scoring_engine.checks.check_test import CheckTest


class TestSMTPSCheck(CheckTest):
    check_name = "SMTPSCheck"
    properties = {
        "touser": "tousr@someone.com",
        "subject": "A scoring engine test subject!",
        "body": "Hello!, This is an email body",
    }
    accounts = {"testuser@emaildomain.com": "passtest"}
    cmd = (
        CHECKS_BIN_PATH
        + "/smtps_check testuser@emaildomain.com passtest testuser@emaildomain.com tousr@someone.com 'A scoring engine test subject!' 'Hello!, This is an email body' 127.0.0.1 1234"
    )
