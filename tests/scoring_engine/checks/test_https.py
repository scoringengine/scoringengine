from tests.scoring_engine.checks.check_test import CheckTest


class TestHTTPSCheck(CheckTest):
    check_name = "HTTPSCheck"
    properties = {"useragent": "testagent", "vhost": "www.example.com", "uri": "/index.html"}
    cmd = "curl -s -S -4 -v -L --cookie-jar - --ssl-reqd --insecure --header 'Host: www.example.com' -A testagent https://127.0.0.1:1234/index.html"
