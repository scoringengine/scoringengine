import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.models.service import Service
from scoring_engine.models.account import Account
from scoring_engine.models.check import Check
from scoring_engine.models.environment import Environment
from scoring_engine.models.round import Round

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from helpers import generate_sample_model_tree
from unit_test import UnitTest


class TestService(UnitTest):

    def test_init_service(self):
        service = Service(name="Example Service", check_name="ICMP IPv4 Check", ip_address='127.0.0.1')
        assert service.id is None
        assert service.name == "Example Service"
        assert service.team is None
        assert service.team is None
        assert service.check_name == "ICMP IPv4 Check"
        assert service.points is None

    def test_basic_service(self):
        team = generate_sample_model_tree('Team', self.db)
        service = Service(name="Example Service", team=team, check_name="ICMP IPv4 Check", ip_address='127.0.0.1')
        self.db.save(service)
        assert service.id is not None
        assert service.name == "Example Service"
        assert service.team == team
        assert service.team_id == team.id
        assert service.check_name == "ICMP IPv4 Check"
        assert service.points == 100

    def test_basic_service_with_points(self):
        team = generate_sample_model_tree('Team', self.db)
        service = Service(name="Example Service", team=team, check_name="ICMP IPv4 Check", points=500, ip_address='127.0.0.1')
        self.db.save(service)
        assert service.id is not None
        assert service.name == "Example Service"
        assert service.team == team
        assert service.team_id == team.id
        assert service.check_name == "ICMP IPv4 Check"
        assert service.points == 500
        assert service.score_earned == 0
        assert service.max_score == 0
        assert service.percent_earned == 0

    def test_last_check_result_false(self):
        team = generate_sample_model_tree('Team', self.db)
        service = Service(name="Example Service", team=team, check_name="ICMP IPv4 Check", ip_address='127.0.0.1')
        self.db.save(service)
        round_obj = generate_sample_model_tree('Round', self.db)
        check_1 = Check(round=round_obj, service=service, result=True, output='Good output')
        self.db.save(check_1)
        check_2 = Check(round=round_obj, service=service, result=True, output='Good output')
        self.db.save(check_2)
        check_3 = Check(round=round_obj, service=service, result=False, output='Check exceeded time')
        self.db.save(check_3)
        assert service.last_check_result() is False

    def test_last_check_result_true(self):
        team = generate_sample_model_tree('Team', self.db)
        service = Service(name="Example Service", team=team, check_name="ICMP IPv4 Check", ip_address='127.0.0.1')
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

    def test_checks_reversed(self):
        service = generate_sample_model_tree('Service', self.db)
        round_obj_1 = Round(number=1)
        round_obj_2 = Round(number=2)
        round_obj_3 = Round(number=3)
        self.db.save(round_obj_1)
        self.db.save(round_obj_2)
        self.db.save(round_obj_3)
        check_1 = Check(round=round_obj_1, service=service)
        self.db.save(check_1)
        check_2 = Check(round=round_obj_2, service=service)
        self.db.save(check_2)
        check_3 = Check(round=round_obj_3, service=service)
        self.db.save(check_3)
        assert service.checks_reversed == [check_3, check_2, check_1]

    def test_environments(self):
        service = generate_sample_model_tree('Service', self.db)
        environment_1 = Environment(service=service, matching_regex='*')
        self.db.save(environment_1)
        environment_2 = Environment(service=service, matching_regex='*')
        self.db.save(environment_2)
        environment_3 = Environment(service=service, matching_regex='*')
        self.db.save(environment_3)
        assert service.environments == [environment_1, environment_2, environment_3]

    def test_accounts(self):
        service = generate_sample_model_tree('Service', self.db)
        account_1 = Account(username="testname", password="testpass", service=service)
        self.db.save(account_1)
        account_2 = Account(username="testname123", password="testpass", service=service)
        self.db.save(account_2)
        account_3 = Account(username="testusername", password="testpass", service=service)
        self.db.save(account_3)
        assert service.accounts == [account_1, account_2, account_3]

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
        assert service.max_score == 500

    def test_percent_earned(self):
        service = generate_sample_model_tree('Service', self.db)
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
        assert service.percent_earned == 80

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
