from tests.scoring_engine.checks.check_test import CheckTest


class TestMYSQLCheck(CheckTest):
    check_name = "MYSQLCheck"
    properties = {"database": "wordpressdb", "command": "show tables"}
    accounts = {"pwnbus": "pwnbuspass"}
    cmd = "mysql -h 127.0.0.1 -P 1234 -u pwnbus -ppwnbuspass wordpressdb -e 'show tables'"
