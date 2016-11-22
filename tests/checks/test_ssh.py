import sys
import os
from scoring_engine.engine.engine import Engine
from scoring_engine.models.service import Service
from scoring_engine.models.property import Property
from tests.scoring_engine.unit_test import UnitTest


class TestSSHCheck(UnitTest):

    def test_ssh_check(self):
        engine = Engine()
        service = Service(name='Example Service', check_name='SSH IPv4 Check', ip_address='127.0.0.1')
        self.db.save(service)
        ssh_check_obj = engine.check_name_to_obj('SSH IPv4 Check')(service)
        assert ssh_check_obj.command() == 'ssh command here'
