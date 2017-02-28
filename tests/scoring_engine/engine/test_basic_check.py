from scoring_engine.engine.basic_check import BasicCheck
from scoring_engine.models.service import Service
from scoring_engine.models.environment import Environment
from scoring_engine.models.account import Account

from tests.scoring_engine.unit_test import UnitTest


class TestBasicCheck(UnitTest):

    def setup(self):
        super(TestBasicCheck, self).setup()
        self.service = Service(name="Example Service", check_name="ICMP IPv4 Check", ip_address='127.0.0.1')
        self.environment = Environment(matching_regex='*', service=self.service)

    def test_init(self):
        check = BasicCheck(self.environment)
        assert check.environment == self.environment
        assert check.required_properties == []

    def test_get_ip_address(self):
        self.db.save(self.service)
        self.db.save(self.environment)
        check = BasicCheck(self.environment)
        assert check.ip_address == '127.0.0.1'

    def test_get_random_account(self):
        self.db.save(Account(username='pwnbus', password='pass', service=self.service))
        self.db.save(self.service)
        self.db.save(self.environment)
        check = BasicCheck(self.environment)
        assert check.get_random_account().username == 'pwnbus'
