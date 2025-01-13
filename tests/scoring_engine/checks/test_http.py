from tests.scoring_engine.checks.check_test import CheckTest


class TestHTTPCheck(CheckTest):
    check_name = "HTTPCheck"
    properties = {"useragent": "testagent", "vhost": "www.example.com", "uri": "/index.html"}
    cmd = "curl -s -S -4 -v -L --cookie-jar - --header 'Host: www.example.com' -A testagent 127.0.0.1:1234/index.html"
