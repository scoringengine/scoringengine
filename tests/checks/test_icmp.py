import sys
import os
from scoring_engine.engine.engine import Engine
from scoring_engine.models.service import Service
from scoring_engine.models.property import Property
from tests.scoring_engine.unit_test import UnitTest


class TestICMPCheck(UnitTest):

    def test_icmp_check(self):
        engine = Engine()
        service = Service(name='Example Service', check_name='ICMP IPv4 Check', ip_address='127.0.0.1')
        self.db.save(service)
        icmp_check_obj = engine.check_name_to_obj('ICMP IPv4 Check')(service)
        assert icmp_check_obj.command() == 'ping -c 1 127.0.0.1'
