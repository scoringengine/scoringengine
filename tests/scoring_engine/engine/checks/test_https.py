from tests.scoring_engine.engine.checks.check_test import CheckTest


class TestHTTPSCheck(CheckTest):
    check_name = 'HTTPSCheck'
    required_properties = ['useragent', 'vhost', 'uri']
    properties = {
        'useragent': 'testagent',
        'vhost': 'www.example.com',
        'uri': '/index.html'
    }
    cmd = "curl -s -S -4 -v -L --header 'Host: www.example.com' -k --ssl-reqd -A 'testagent' '127.0.0.1:100/index.html'"
