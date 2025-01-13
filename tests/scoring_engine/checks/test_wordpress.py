from tests.scoring_engine.checks.check_test import CheckTest


class TestWordpressCheck(CheckTest):
    check_name = "WordpressCheck"
    properties = {"useragent": "testagent", "vhost": "www.example.com", "uri": "/wp-login.php"}
    accounts = {"admin": "password"}
    cmd = (
        "curl -s -S -4 -v -L --cookie-jar - --header 'Host: www.example.com' -A 'testagent' "
        "--data 'log=admin&pwd=password' '127.0.0.1:1234/wp-login.php'"
    )
