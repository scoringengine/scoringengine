from scoring_engine.engine.engine import Engine
from scoring_engine.models.service import Service
from scoring_engine.models.environment import Environment
from scoring_engine.models.property import Property
from scoring_engine.models.account import Account

import pytest

from tests.scoring_engine.unit_test import UnitTest


class CheckTest(UnitTest):

    def setup(self):
        super(CheckTest, self).setup()
        self.engine = Engine()
        self.service = Service(name='Example Service', check_name=self.check_name, ip_address='127.0.0.1')
        self.environment = Environment(service=self.service, matching_regex='*')
        if not hasattr(self, 'properties'):
            self.properties = {}
        if not hasattr(self, 'accounts'):
            self.accounts = {}
        for property_name, property_value in self.properties.items():
            self.db.save(Property(environment=self.environment, name=property_name, value=property_value))
        for account_name, account_pass in self.accounts.items():
            self.db.save(Account(username=account_name, password=account_pass, service=self.service))
        self.db.save(self.service)
        self.db.save(self.environment)

    def test_bad_properties(self):
        environment = Environment(service=self.service, matching_regex='*')
        self.db.save(environment)
        self.service.environments = [environment]
        temp_properties = dict(self.properties)
        if len(temp_properties) > 0:
            temp_properties.popitem()
        else:
            temp_properties['exampleproperty'] = 'propertyvalueexample'
        for property_name, property_value in temp_properties.items():
            property_obj = Property(environment=environment, name=property_name, value=property_value)
            self.db.save(property_obj)
        with pytest.raises(LookupError):
            self.engine.check_name_to_obj(self.check_name)(environment)

    def test_cmd(self):
        check_obj = self.engine.check_name_to_obj(self.check_name)(self.environment)
        assert check_obj.command() == self.cmd
