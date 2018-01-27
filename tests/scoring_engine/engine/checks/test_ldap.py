from tests.scoring_engine.engine.checks.check_test import CheckTest


class TestLDAPCheck(CheckTest):
    check_name = 'LDAPCheck'
    properties = {
        'domain': 'example.com',
        'base_dn': 'dc=example,dc=com'
    }
    accounts = {
        'testuser': 'testpass'
    }
    cmd = "ldapsearch -x -h '127.0.0.1' -p 100 -D 'testuser'@'example.com' -b 'dc=example,dc=com' -w 'testpass'"
