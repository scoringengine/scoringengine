from tests.scoring_engine.checks.check_test import CheckTest


class TestLDAPCheck(CheckTest):
    check_name = "LDAPCheck"
    properties = {"domain": "example.com", "base_dn": "dc=example,dc=com"}
    accounts = {"testuser": "testpass"}
    cmd = "ldapsearch -x -h 127.0.0.1 -p 1234 -D testuser@example.com -b dc=example,dc=com -w testpass '(objectclass=User)' cn"
