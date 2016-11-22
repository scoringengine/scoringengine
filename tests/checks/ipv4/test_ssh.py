import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.engine.engine import Engine
from scoring_engine.models.service import Service

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../scoring_engine'))
from unit_test import UnitTest


class TestSSHCheck(UnitTest):

    def test_ssh_check(self):
        engine = Engine()
        service = Service(name="Example Service", check_name="SSH IPv4 Check", ip_address='127.0.0.1')
        self.db.save(service)
        ssh_check_obj = engine.checks[1](service)
        assert ssh_check_obj.command() == 'ssh command here'
