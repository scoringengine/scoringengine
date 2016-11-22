import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.engine.basic_check import BasicCheck
from scoring_engine.models.service import Service
from scoring_engine.models.environment import Environment

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from unit_test import UnitTest


class TestBasicCheck(UnitTest):

    def test_init(self):
        service = Service(name="Example Service", check_name="ICMP IPv4 Check", ip_address='127.0.0.1')
        check = BasicCheck(service)
        assert check.service == service

    def test_properties(self):
        service = Service(name="Example Service", check_name="ICMP IPv4 Check", ip_address='127.0.0.1')
        environment_1 = Environment(matching_regex='*', service=service)
        environment_2 = Environment(matching_regex='*', service=service)
        self.db.save(service)
        self.db.save(environment_1)
        self.db.save(environment_2)
        check = BasicCheck(service)
        assert check.environments() == [environment_1, environment_2]

    def test_get_ip_address_good(self):
        service = Service(name="Example Service", check_name="ICMP IPv4 Check", ip_address='127.0.0.4')
        self.db.save(service)
        check = BasicCheck(service)
        assert check.get_ip_address() == '127.0.0.4'
