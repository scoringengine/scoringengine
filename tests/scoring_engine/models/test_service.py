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
        assert service.points == None

    def test_basic_service(self):
        team = generate_sample_model_tree('Team', self.db)
        service = Service(name="Example Service", team=team, check_name="ICMP IPv4 Check")
        self.db.save(service)
        assert service.id is not None
        assert service.name == "Example Service"
        assert service.team == team
        assert service.team_id == team.id
        assert service.check_name == "ICMP IPv4 Check"
        assert service.points == 100

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

    def test_score_earned(self):
        service = generate_sample_model_tree('Service', self.db)
        check_1 = Check(service=service, result=True, output='Good output')
        check_2 = Check(service=service, result=True, output='Good output')
        check_3 = Check(service=service, result=True, output='Good output')
        check_4 = Check(service=service, result=True, output='Good output')
        check_5 = Check(service=service, result=False, output='bad output')
        self.db.save(check_1)
        self.db.save(check_2)
        self.db.save(check_3)
        self.db.save(check_4)
        self.db.save(check_5)
        assert service.score_earned == 400

    def test_max_score(self):
        service = generate_sample_model_tree('Service', self.db)
        assert service.max_score == 1000

    def test_percent_earned(self):
        service = generate_sample_model_tree('Service', self.db)
        assert service.percent_earned == 40

    def test_last_ten_checks_4_checks(self):
        service = generate_sample_model_tree('Service', self.db)
        check_1 = Check(service=service, result=True, output='Good output')
        check_2 = Check(service=service, result=True, output='Good output')
        check_3 = Check(service=service, result=True, output='Good output')
        check_4 = Check(service=service, result=True, output='Good output')
        self.db.save(check_1)
        self.db.save(check_2)
        self.db.save(check_3)
        self.db.save(check_4)
        assert service.last_ten_checks == [check_4, check_3, check_2, check_1]
        assert service.percent_earned == 40

    def test_last_ten_checks_15_checks(self):
        service = generate_sample_model_tree('Service', self.db)
        check_1 = Check(service=service, result=True, output='Good output')
        check_2 = Check(service=service, result=True, output='Good output')
        check_3 = Check(service=service, result=True, output='Good output')
        check_4 = Check(service=service, result=True, output='Good output')
        check_5 = Check(service=service, result=True, output='Good output')
        check_6 = Check(service=service, result=True, output='Good output')
        check_7 = Check(service=service, result=True, output='Good output')
        check_8 = Check(service=service, result=True, output='Good output')
        check_9 = Check(service=service, result=True, output='Good output')
        check_10 = Check(service=service, result=True, output='Good output')
        check_11 = Check(service=service, result=True, output='Good output')
        check_12 = Check(service=service, result=True, output='Good output')
        check_13 = Check(service=service, result=True, output='Good output')
        check_14 = Check(service=service, result=True, output='Good output')
        check_15 = Check(service=service, result=True, output='Good output')
        self.db.save(check_1)
        self.db.save(check_2)
        self.db.save(check_3)
        self.db.save(check_4)
        self.db.save(check_5)
        self.db.save(check_6)
        self.db.save(check_7)
        self.db.save(check_8)
        self.db.save(check_9)
        self.db.save(check_10)
        self.db.save(check_11)
        self.db.save(check_12)
        self.db.save(check_13)
        self.db.save(check_14)
        self.db.save(check_15)
        assert service.last_ten_checks == [
            check_15,
            check_14,
            check_13,
            check_12,
            check_11,
            check_10,
            check_9,
            check_8,
            check_7,
            check_6
        ]
