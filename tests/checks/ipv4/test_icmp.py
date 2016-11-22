import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.engine.engine import Engine
from scoring_engine.models.service import Service

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../scoring_engine'))
from unit_test import UnitTest


class TestICMPCheck(UnitTest):

    def test_icmp_check(self):
        engine = Engine()
        service = Service(name="Example Service", check_name="ICMP IPv4 Check", ip_address='127.0.0.1')
        self.db.save(service)
        icmp_check_obj = engine.checks[0](service)
        assert icmp_check_obj.command() == 'ping -c 1 127.0.0.1'
