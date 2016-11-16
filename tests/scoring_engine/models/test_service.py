import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.models.service import Service
from scoring_engine.models.check import Check
from scoring_engine.models.property import Property

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from helpers import generate_sample_model_tree
from unit_test import UnitTest


class TestService(UnitTest):

    def test_init_service(self):
        service = Service(name="Example Service", check_name="ICMP IPv4 Check")
        assert service.id is None
        assert service.name == "Example Service"
        assert service.team is None
        assert service.team is None
        assert service.check_name == "ICMP IPv4 Check"

    def test_basic_service(self):
        team = generate_sample_model_tree('Team', self.db)
        service = Service(name="Example Service", team=team, check_name="ICMP IPv4 Check")
        self.db.save(service)
        assert service.id is not None
        assert service.name == "Example Service"
        assert service.team == team
        assert service.team_id == team.id
        assert service.check_name == "ICMP IPv4 Check"

    def test_false_service_result(self):
        team = generate_sample_model_tree('Team', self.db)
        service = Service(name="Example Service", team=team, check_name="ICMP IPv4 Check")
        self.db.save(service)
        round_obj = generate_sample_model_tree('Round', self.db)
        check_1 = Check(round=round_obj, service=service, result=True, output='Good output')
        self.db.save(check_1)
        check_2 = Check(round=round_obj, service=service, result=True, output='Good output')
        self.db.save(check_2)
        check_3 = Check(round=round_obj, service=service, result=False, output='Check exceeded time')
        self.db.save(check_3)
        assert service.last_check_result() is False

    def test_false_service_result(self):
        team = generate_sample_model_tree('Team', self.db)
        service = Service(name="Example Service", team=team, check_name="ICMP IPv4 Check")
        self.db.save(service)
        round_obj = generate_sample_model_tree('Round', self.db)
        check_1 = Check(round=round_obj, service=service, result=False, output='Check exceeded time')
        self.db.save(check_1)
        check_2 = Check(round=round_obj, service=service, result=False, output='Check exceeded time')
        self.db.save(check_2)
        check_3 = Check(round=round_obj, service=service, result=True, output='Good output')
        self.db.save(check_3)
        assert service.last_check_result() is True

    def test_checks(self):
        service = generate_sample_model_tree('Service', self.db)
        round_obj = generate_sample_model_tree('Round', self.db)
        check_1 = Check(round=round_obj, service=service)
        self.db.save(check_1)
        check_2 = Check(round=round_obj, service=service)
        self.db.save(check_2)
        check_3 = Check(round=round_obj, service=service)
        self.db.save(check_3)
        assert service.checks == [check_1, check_2, check_3]

    def test_properties(self):
        service = generate_sample_model_tree('Service', self.db)
        property_1 = Property(name="ip", value="127.0.0.1", service=service)
        self.db.save(property_1)
        property_2 = Property(name="username", value="testuser", service=service)
        self.db.save(property_2)
        property_3 = Property(name="password", value="testpass", service=service)
        self.db.save(property_3)
        assert service.properties == [property_1, property_2, property_3]
