from tests.scoring_engine.checks.check_test import CheckTest


class TestMSSQLCheck(CheckTest):
    check_name = "MSSQLCheck"
    properties = {"database": "master", "command": "SELECT @@version"}
    accounts = {"pwnbus": "pwnbuspass"}
    cmd = "SQLCMDPASSWORD=pwnbuspass sqlcmd -S 127.0.0.1,1234 -U pwnbus -d master -Q 'SELECT @@version'"
