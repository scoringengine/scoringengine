from tests.scoring_engine.checks.check_test import CheckTest


class TestDNSCheck(CheckTest):
    check_name = 'DNSCheck'
    properties = {
        'qtype': 'A',
        'domain': 'www.google.com'
    }
    cmd = "dig @'127.0.0.1' -p 1234 -t 'A' -q 'www.google.com'"
