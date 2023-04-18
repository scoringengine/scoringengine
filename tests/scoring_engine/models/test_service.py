from scoring_engine.models.team import Team
from scoring_engine.models.service import Service
from scoring_engine.models.account import Account
from scoring_engine.models.check import Check
from scoring_engine.models.environment import Environment
from scoring_engine.models.round import Round

from tests.scoring_engine.helpers import generate_sample_model_tree
from tests.scoring_engine.unit_test import UnitTest


class TestService(UnitTest):

    def test_init_service(self):
        service = Service(name="Example Service", check_name="ICMP IPv4 Check", host='127.0.0.1')
        assert service.id is None
        assert service.name == "Example Service"
        assert service.team is None
        assert service.team is None
        assert service.check_name == "ICMP IPv4 Check"
        assert service.points is None

    def test_basic_service(self):
        team = generate_sample_model_tree('Team', self.session)
        service = Service(name="Example Service", team=team, check_name="ICMP IPv4 Check", host='127.0.0.1')
        self.session.add(service)
        self.session.commit()
        assert service.id is not None
        assert service.name == "Example Service"
        assert service.team == team
        assert service.team_id == team.id
        assert service.check_name == "ICMP IPv4 Check"
        assert service.port == 0
        assert service.points == 100
        assert service.worker_queue == 'main'

    def test_basic_service_with_worker_queue(self):
        team = generate_sample_model_tree('Team', self.session)
        service = Service(name="Example Service", team=team, check_name="ICMP IPv4 Check", host='127.0.0.1', worker_queue='somequeue')
        self.session.add(service)
        self.session.commit()
        assert service.id is not None
        assert service.name == "Example Service"
        assert service.team == team
        assert service.team_id == team.id
        assert service.check_name == "ICMP IPv4 Check"
        assert service.port == 0
        assert service.points == 100
        assert service.worker_queue == 'somequeue'

    def test_basic_service_with_points(self):
        team = generate_sample_model_tree('Team', self.session)
        service = Service(name="Example Service", team=team, check_name="ICMP IPv4 Check", points=500, host='127.0.0.1', port=100)
        self.session.add(service)
        self.session.commit()
        assert service.id is not None
        assert service.name == "Example Service"
        assert service.team == team
        assert service.team_id == team.id
        assert service.check_name == "ICMP IPv4 Check"
        assert service.port == 100
        assert service.points == 500
        assert service.score_earned == 0
        assert service.max_score == 0
        assert service.percent_earned == 0

    def test_last_check_result_false(self):
        team = generate_sample_model_tree('Team', self.session)
        service = Service(name="Example Service", team=team, check_name="ICMP IPv4 Check", host='127.0.0.1')
        self.session.add(service)
        round_obj = generate_sample_model_tree('Round', self.session)
        check_1 = Check(round=round_obj, service=service, result=True, output='Good output')
        self.session.add(check_1)
        check_2 = Check(round=round_obj, service=service, result=True, output='Good output')
        self.session.add(check_2)
        check_3 = Check(round=round_obj, service=service, result=False, output='Check exceeded time')
        self.session.add(check_3)
        self.session.commit()
        assert service.last_check_result() is False

    def test_last_check_result_true(self):
        team = generate_sample_model_tree('Team', self.session)
        service = Service(name="Example Service", team=team, check_name="ICMP IPv4 Check", host='127.0.0.1')
        self.session.add(service)
        round_obj = generate_sample_model_tree('Round', self.session)
        check_1 = Check(round=round_obj, service=service, result=False, output='Check exceeded time')
        self.session.add(check_1)
        check_2 = Check(round=round_obj, service=service, result=False, output='Check exceeded time')
        self.session.add(check_2)
        check_3 = Check(round=round_obj, service=service, result=True, output='Good output')
        self.session.add(check_3)
        self.session.commit()
        assert service.last_check_result() is True

    def test_last_check_result_not_found(self):
        team = generate_sample_model_tree('Team', self.session)
        service = Service(name="Example Service", team=team, check_name="ICMP IPv4 Check", host='127.0.0.1')
        self.session.add(service)
        self.session.commit()
        assert service.last_check_result() is None

    def test_checks(self):
        service = generate_sample_model_tree('Service', self.session)
        round_obj = generate_sample_model_tree('Round', self.session)
        check_1 = Check(round=round_obj, service=service)
        self.session.add(check_1)
        check_2 = Check(round=round_obj, service=service)
        self.session.add(check_2)
        check_3 = Check(round=round_obj, service=service)
        self.session.add(check_3)
        self.session.commit()
        assert service.checks == [check_1, check_2, check_3]

    def test_checks_reversed(self):
        service = generate_sample_model_tree('Service', self.session)
        round_obj_1 = Round(number=1)
        round_obj_2 = Round(number=2)
        round_obj_3 = Round(number=3)
        self.session.add(round_obj_1)
        self.session.add(round_obj_2)
        self.session.add(round_obj_3)
        check_1 = Check(round=round_obj_1, service=service)
        self.session.add(check_1)
        check_2 = Check(round=round_obj_2, service=service)
        self.session.add(check_2)
        check_3 = Check(round=round_obj_3, service=service)
        self.session.add(check_3)
        self.session.commit()
        assert service.checks_reversed == [check_3, check_2, check_1]

    def test_environments(self):
        service = generate_sample_model_tree('Service', self.session)
        environment_1 = Environment(service=service, matching_content='*')
        self.session.add(environment_1)
        environment_2 = Environment(service=service, matching_content='*')
        self.session.add(environment_2)
        environment_3 = Environment(service=service, matching_content='*')
        self.session.add(environment_3)
        self.session.commit()
        assert service.environments == [environment_1, environment_2, environment_3]

    def test_accounts(self):
        service = generate_sample_model_tree('Service', self.session)
        account_1 = Account(username="testname", password="testpass", service=service)
        self.session.add(account_1)
        account_2 = Account(username="testname123", password="testpass", service=service)
        self.session.add(account_2)
        account_3 = Account(username="testusername", password="testpass", service=service)
        self.session.add(account_3)
        self.session.commit()
        assert service.accounts == [account_1, account_2, account_3]

    def test_score_earned(self):
        service = generate_sample_model_tree('Service', self.session)
        check_1 = Check(service=service, result=True, output='Good output')
        check_2 = Check(service=service, result=True, output='Good output')
        check_3 = Check(service=service, result=True, output='Good output')
        check_4 = Check(service=service, result=True, output='Good output')
        check_5 = Check(service=service, result=False, output='bad output')
        self.session.add(check_1)
        self.session.add(check_2)
        self.session.add(check_3)
        self.session.add(check_4)
        self.session.add(check_5)
        self.session.commit()
        assert service.score_earned == 400

    def test_max_score(self):
        service = generate_sample_model_tree('Service', self.session)
        check_1 = Check(service=service, result=True, output='Good output')
        check_2 = Check(service=service, result=True, output='Good output')
        check_3 = Check(service=service, result=True, output='Good output')
        check_4 = Check(service=service, result=True, output='Good output')
        check_5 = Check(service=service, result=False, output='bad output')
        self.session.add(check_1)
        self.session.add(check_2)
        self.session.add(check_3)
        self.session.add(check_4)
        self.session.add(check_5)
        self.session.commit()
        assert service.max_score == 500

    def test_percent_earned(self):
        service = generate_sample_model_tree('Service', self.session)
        service = generate_sample_model_tree('Service', self.session)
        check_1 = Check(service=service, result=True, output='Good output')
        check_2 = Check(service=service, result=True, output='Good output')
        check_3 = Check(service=service, result=True, output='Good output')
        check_4 = Check(service=service, result=True, output='Good output')
        check_5 = Check(service=service, result=False, output='bad output')
        self.session.add(check_1)
        self.session.add(check_2)
        self.session.add(check_3)
        self.session.add(check_4)
        self.session.add(check_5)
        self.session.commit()
        assert service.percent_earned == 80

    def test_last_ten_checks_4_checks(self):
        service = generate_sample_model_tree('Service', self.session)
        check_1 = Check(service=service, result=True, output='Good output')
        check_2 = Check(service=service, result=True, output='Good output')
        check_3 = Check(service=service, result=True, output='Good output')
        check_4 = Check(service=service, result=True, output='Good output')
        self.session.add(check_1)
        self.session.add(check_2)
        self.session.add(check_3)
        self.session.add(check_4)
        self.session.commit()
        assert service.last_ten_checks == [check_4, check_3, check_2, check_1]

    def test_last_ten_checks_15_checks(self):
        service = generate_sample_model_tree('Service', self.session)
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
        self.session.add(check_1)
        self.session.add(check_2)
        self.session.add(check_3)
        self.session.add(check_4)
        self.session.add(check_5)
        self.session.add(check_6)
        self.session.add(check_7)
        self.session.add(check_8)
        self.session.add(check_9)
        self.session.add(check_10)
        self.session.add(check_11)
        self.session.add(check_12)
        self.session.add(check_13)
        self.session.add(check_14)
        self.session.add(check_15)
        self.session.commit()
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

    def test_check_result_for_round_no_rounds(self):
        service = Service(name="Example Service", check_name="ICMP IPv4 Check", host='127.0.0.1')
        assert service.check_result_for_round(1) is False

    def test_check_result_for_round_3_rounds(self):
        service = generate_sample_model_tree('Service', self.session)

        round_1 = Round(number=1)
        self.session.add(round_1)
        check_1 = Check(round=round_1, result=True, service=service)
        self.session.add(check_1)

        round_2 = Round(number=2)
        self.session.add(round_2)
        check_2 = Check(round=round_2, result=True, service=service)
        self.session.add(check_2)

        round_3 = Round(number=3)
        self.session.add(round_3)
        check_3 = Check(round=round_3, result=False, service=service)
        self.session.add(check_3)
        self.session.commit()
        assert service.check_result_for_round(1) is True
        assert service.check_result_for_round(2) is True
        assert service.check_result_for_round(3) is False

    def test_rank(self):
        team_1 = Team(name="Blue Team 1", color="Blue")
        self.session.add(team_1)
        service_1 = Service(name="Example Service 1", team=team_1, check_name="ICMP IPv4 Check", host='127.0.0.1')
        self.session.add(service_1)
        check_1 = Check(service=service_1, result=True, output='Good output')
        check_2 = Check(service=service_1, result=True, output='Good output')
        self.session.add(check_1)
        self.session.add(check_2)
        self.session.commit()

        team_2 = Team(name="Blue Team 2", color="Blue")
        self.session.add(team_2)
        service_1 = Service(name="Example Service 1", team=team_2, check_name="ICMP IPv4 Check", host='127.0.0.1')
        self.session.add(service_1)
        check_1 = Check(service=service_1, result=True, output='Good output')
        check_2 = Check(service=service_1, result=True, output='Good output')
        self.session.add(check_1)
        self.session.add(check_2)
        self.session.commit()

        team_3 = Team(name="Blue Team 3", color="Blue")
        self.session.add(team_3)
        service_1 = Service(name="Example Service 1", team=team_3, check_name="ICMP IPv4 Check", host='127.0.0.1')
        self.session.add(service_1)
        check_1 = Check(service=service_1, result=True, output='Good output')
        check_2 = Check(service=service_1, result=False, output='Good output')
        self.session.add(check_1)
        self.session.add(check_2)
        self.session.commit()
        assert team_1.services[0].rank == 1
        assert team_2.services[0].rank == 1
        assert team_3.services[0].rank == 3

    def test_rank_no_scores(self):
        team_1 = Team(name="Blue Team 1", color="Blue")
        self.session.add(team_1)
        service_1 = Service(name="Example Service 1", team=team_1, check_name="ICMP IPv4 Check", host='127.0.0.1')
        self.session.add(service_1)
        self.session.commit()

        team_2 = Team(name="Blue Team 2", color="Blue")
        self.session.add(team_2)
        service_1 = Service(name="Example Service 1", team=team_2, check_name="ICMP IPv4 Check", host='127.0.0.1')
        self.session.add(service_1)
        self.session.commit()

        team_3 = Team(name="Blue Team 3", color="Blue")
        self.session.add(team_3)
        service_1 = Service(name="Example Service 1", team=team_3, check_name="ICMP IPv4 Check", host='127.0.0.1')
        self.session.add(service_1)
        self.session.commit()

        assert team_1.services[0].rank == None
        assert team_2.services[0].rank == None
        assert team_3.services[0].rank == None

    def test_rank_no_team_scores(self):
        team_1 = Team(name="Blue Team 1", color="Blue")
        self.session.add(team_1)
        service_1 = Service(name="Example Service 1", team=team_1, check_name="ICMP IPv4 Check", host='127.0.0.1')
        self.session.add(service_1)
        check_1 = Check(service=service_1, result=True, output='Good output')
        check_2 = Check(service=service_1, result=True, output='Good output')
        self.session.add(check_1)
        self.session.add(check_2)
        self.session.commit()

        team_2 = Team(name="Blue Team 2", color="Blue")
        self.session.add(team_2)
        service_1 = Service(name="Example Service 1", team=team_2, check_name="ICMP IPv4 Check", host='127.0.0.1')
        self.session.add(service_1)
        check_1 = Check(service=service_1, result=True, output='Good output')
        check_2 = Check(service=service_1, result=True, output='Good output')
        self.session.add(check_1)
        self.session.add(check_2)
        self.session.commit()

        team_3 = Team(name="Blue Team 3", color="Blue")
        self.session.add(team_3)
        service_1 = Service(name="Example Service 1", team=team_3, check_name="ICMP IPv4 Check", host='127.0.0.1')
        self.session.add(service_1)
        self.session.commit()

        assert team_1.services[0].rank == 1
        assert team_2.services[0].rank == 1
        assert team_3.services[0].rank == None
