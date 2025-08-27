from tests.scoring_engine.checks.check_test import CheckTest


class TestLDAPCheck(CheckTest):
    check_name = "LDAPCheck"
    properties = {"domain_base": "dc=example,dc=com"}
    accounts = {"testuser": "testpass"}
    cmd = "ldapsearch -x -H ldap://127.0.0.1:1234 -D cn=testuser,cn=Users,dc=example,dc=com -w testpass -b dc=example,dc=com '(objectclass=Domain)' cn"
