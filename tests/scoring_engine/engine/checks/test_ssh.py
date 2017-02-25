from scoring_engine.engine.engine import Engine
from scoring_engine.models.service import Service
from scoring_engine.models.environment import Environment

from tests.scoring_engine.unit_test import UnitTest


class TestSSHCheck(UnitTest):

    def test_ssh_check(self):
        engine = Engine()
        service = Service(name='Example Service', check_name='SSHCheck', ip_address='127.0.0.1')
        environment = Environment(matching_regex='*')
        self.db.save(service)
        self.db.save(environment)
        ssh_check_obj = engine.check_name_to_obj('SSHCheck')(environment)
        assert ssh_check_obj.command() == 'ssh command here'
