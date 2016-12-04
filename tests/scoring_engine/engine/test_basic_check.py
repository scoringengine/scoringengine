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
        environment = Environment(matching_regex='*')
        check = BasicCheck(environment)
        assert check.environment == environment

    def test_get_ip_address_good(self):
        service = Service(name="Example Service", check_name="ICMP IPv4 Check", ip_address='127.0.0.4')
        self.db.save(service)
        environment = Environment(matching_regex='*', service=service)
        self.db.save(environment)
        check = BasicCheck(environment)
        assert check.get_ip_address() == '127.0.0.4'
