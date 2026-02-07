from tests.scoring_engine.checks.check_test import CheckTest


class TestPOSTGRESQLCheck(CheckTest):
    check_name = "POSTGRESQLCheck"
    properties = {"database": "testdb", "command": r"\d"}
    accounts = {"pwnbus": "pwnbuspass"}
    cmd = r"PGPASSWORD=pwnbuspass psql -h 127.0.0.1 -p 1234 -U pwnbus -c '\d' testdb"
