import pytest

from scoring_engine.engine.basic_check import BasicCheck
from scoring_engine.models.service import Service
from scoring_engine.models.environment import Environment
from scoring_engine.models.account import Account

from tests.scoring_engine.unit_test import UnitTest


class TestBasicCheck(UnitTest):

    def setup(self):
        super(TestBasicCheck, self).setup()
        self.service = Service(name="Example Service", check_name="ICMP IPv4 Check", host='127.0.0.1')
        self.environment = Environment(matching_content='*', service=self.service)

    def test_init(self):
        check = BasicCheck(self.environment)
        assert check.environment == self.environment
        assert check.required_properties == []

    def test_get_host(self):
        self.session.add(self.service)
        self.session.add(self.environment)
        self.session.commit()
        check = BasicCheck(self.environment)
        assert check.host == '127.0.0.1'

    def test_get_random_account(self):
        self.session.add(Account(username='pwnbus', password='pass', service=self.service))
        self.session.add(self.service)
        self.session.add(self.environment)
        self.session.commit()
        check = BasicCheck(self.environment)
        assert check.get_random_account().username == 'pwnbus'

    def test_check_no_properties(self):
        check = BasicCheck(self.environment)
        check.required_properties = ['testparam']
        with pytest.raises(LookupError):
            check.set_properties()
