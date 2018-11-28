from scoring_engine.engine.engine import Engine
from scoring_engine.models.service import Service
from scoring_engine.models.environment import Environment
from scoring_engine.models.property import Property
from scoring_engine.models.account import Account

from tests.scoring_engine.unit_test import UnitTest


class CheckTest(UnitTest):

    def test_cmd(self):
        engine = Engine()
        service = Service(name='Example Service', check_name=self.check_name, host='127.0.0.1', port=1234)
        environment = Environment(service=service, matching_content='*')
        if not hasattr(self, 'properties'):
            self.properties = {}
        if not hasattr(self, 'accounts'):
            self.accounts = {}
        for property_name, property_value in self.properties.items():
            self.session.add(Property(environment=environment, name=property_name, value=property_value))
        for account_name, account_pass in self.accounts.items():
            self.session.add(Account(username=account_name, password=account_pass, service=service))
        self.session.add(service)
        self.session.add(environment)
        self.session.commit()

        check_obj = engine.check_name_to_obj(self.check_name)(environment)
        assert check_obj.command() == self.cmd
