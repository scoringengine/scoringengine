import pytest

from scoring_engine.engine.engine import Engine
from scoring_engine.models.service import Service
from scoring_engine.models.environment import Environment
from scoring_engine.models.property import Property
from tests.scoring_engine.unit_test import UnitTest


class TestDNSCheck(UnitTest):
    def test_dns_check(self):
        engine = Engine()
        service = Service(name='Example Service', check_name='DNS IPv4 Check', ip_address='127.0.0.1')
        environment = Environment(service=service, matching_regex='IN   A')
        prop1 = Property(environment=environment, name='qtype', value='A')
        prop2 = Property(environment=environment, name='domain', value='www.google.com')
        self.db.save(service)
        self.db.save(environment)
        self.db.save(prop1)
        self.db.save(prop2)
        dns_check_obj = engine.check_name_to_obj('DNS IPv4 Check')(environment)
        assert dns_check_obj.command() == 'dig @127.0.0.1 -t A -q www.google.com'

    def test_dns_check_not_enough_properties(self):
        engine = Engine()
        service = Service(name='Example Service', check_name='DNS IPv4 Check', ip_address='127.0.0.1')
        environment = Environment(service=service, matching_regex='IN   A')
        prop1 = Property(environment=environment, name='qtype', value='A')
        self.db.save(service)
        self.db.save(environment)
        self.db.save(prop1)
        dns_check_obj = engine.check_name_to_obj('DNS IPv4 Check')(environment)
        with pytest.raises(LookupError):
            dns_check_obj.command()