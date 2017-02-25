from scoring_engine.engine.engine import Engine
from scoring_engine.models.service import Service
from scoring_engine.models.environment import Environment
from tests.scoring_engine.unit_test import UnitTest


class TestICMPCheck(UnitTest):

    def test_icmp_check(self):
        engine = Engine()
        service = Service(name='Example Service', check_name='ICMPCheck', ip_address='127.0.0.1')
        environment = Environment(matching_regex='*', service=service)
        self.db.save(service)
        self.db.save(environment)
        icmp_check_obj = engine.check_name_to_obj('ICMPCheck')(environment)
        assert icmp_check_obj.command() == 'ping -c 1 127.0.0.1'
