from tests.scoring_engine.engine.checks.check_test import CheckTest


class TestHTTPCheck(CheckTest):
    check_name = 'HTTPCheck'
    required_properties = ['useragent', 'vhost', 'uri']
    properties = {
        'useragent': 'testagent',
        'vhost': 'www.example.com',
        'uri': '/index.html'
    }
    cmd = "curl -s -S -4 -v -L -A 'testagent' 'http://www.example.com:100/index.html'"
