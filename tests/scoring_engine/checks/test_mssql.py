from tests.scoring_engine.checks.check_test import CheckTest


class TestMSSQLCheck(CheckTest):
    check_name = 'MSSQLCheck'
    properties = {
        'database': 'master',
        'command': 'SELECT @@version'
    }
    accounts = {
        'pwnbus': 'pwnbuspass'
    }
    cmd = "/opt/mssql-tools/bin/sqlcmd -S '127.0.0.1',1234 -U 'pwnbus' -P 'pwnbuspass' -d 'master' -Q 'SELECT @@version'"
