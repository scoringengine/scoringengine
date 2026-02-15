import pytest

from scoring_engine.db import db
from scoring_engine.engine.basic_check import BasicCheck
from scoring_engine.models.account import Account
from scoring_engine.models.environment import Environment
from scoring_engine.models.service import Service


class TestBasicCheck:

    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        self.service = Service(name="Example Service", check_name="ICMP IPv4 Check", host="127.0.0.1")
        self.environment = Environment(matching_content="*", service=self.service)

    def test_init(self):
        check = BasicCheck(self.environment)
        assert check.environment == self.environment
        assert check.required_properties == []

    def test_get_host(self):
        db.session.add(self.service)
        db.session.add(self.environment)
        db.session.commit()
        check = BasicCheck(self.environment)
        assert check.host == "127.0.0.1"

    def test_get_random_account(self):
        db.session.add(Account(username="pwnbus", password="pass", service=self.service))
        db.session.add(self.service)
        db.session.add(self.environment)
        db.session.commit()
        check = BasicCheck(self.environment)
        assert check.get_random_account().username == "pwnbus"

    def test_check_no_properties(self):
        check = BasicCheck(self.environment)
        check.required_properties = ["testparam"]
        with pytest.raises(LookupError):
            check.set_properties()
