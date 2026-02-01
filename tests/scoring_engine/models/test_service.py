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

    # Service Dependency Tests

    def test_service_no_parent(self):
        """Test service with no parent dependency."""
        service = generate_sample_model_tree('Service', self.session)
        assert service.parent is None
        assert service.parent_id is None
        assert service.parent_is_down() is False
        assert service.get_root_cause() is None
        assert service.get_dependency_chain() == []

    def test_service_with_parent(self):
        """Test setting a parent service."""
        team = generate_sample_model_tree('Team', self.session)
        parent_service = Service(name="DNS", team=team, check_name="DNS Check", host='127.0.0.1')
        child_service = Service(name="HTTP", team=team, check_name="HTTP Check", host='127.0.0.1')
        self.session.add(parent_service)
        self.session.add(child_service)
        self.session.commit()

        child_service.parent = parent_service
        self.session.commit()

        assert child_service.parent == parent_service
        assert child_service.parent_id == parent_service.id
        assert parent_service.children == [child_service]

    def test_parent_is_down_when_parent_fails(self):
        """Test parent_is_down returns True when parent's last check failed."""
        team = generate_sample_model_tree('Team', self.session)
        round_obj = generate_sample_model_tree('Round', self.session)

        parent_service = Service(name="DNS", team=team, check_name="DNS Check", host='127.0.0.1')
        child_service = Service(name="HTTP", team=team, check_name="HTTP Check", host='127.0.0.1')
        self.session.add(parent_service)
        self.session.add(child_service)
        self.session.commit()

        child_service.parent = parent_service
        # Parent service check fails
        check = Check(round=round_obj, service=parent_service, result=False, output='Failed')
        self.session.add(check)
        self.session.commit()

        assert child_service.parent_is_down() is True

    def test_parent_is_down_when_parent_passes(self):
        """Test parent_is_down returns False when parent's last check passed."""
        team = generate_sample_model_tree('Team', self.session)
        round_obj = generate_sample_model_tree('Round', self.session)

        parent_service = Service(name="DNS", team=team, check_name="DNS Check", host='127.0.0.1')
        child_service = Service(name="HTTP", team=team, check_name="HTTP Check", host='127.0.0.1')
        self.session.add(parent_service)
        self.session.add(child_service)
        self.session.commit()

        child_service.parent = parent_service
        # Parent service check passes
        check = Check(round=round_obj, service=parent_service, result=True, output='OK')
        self.session.add(check)
        self.session.commit()

        assert child_service.parent_is_down() is False

    def test_get_root_cause_with_failing_parent(self):
        """Test get_root_cause returns the failing parent."""
        team = generate_sample_model_tree('Team', self.session)
        round_obj = generate_sample_model_tree('Round', self.session)

        dns_service = Service(name="DNS", team=team, check_name="DNS Check", host='127.0.0.1')
        http_service = Service(name="HTTP", team=team, check_name="HTTP Check", host='127.0.0.1')
        self.session.add(dns_service)
        self.session.add(http_service)
        self.session.commit()

        http_service.parent = dns_service
        # DNS fails
        check = Check(round=round_obj, service=dns_service, result=False, output='Failed')
        self.session.add(check)
        self.session.commit()

        root_cause = http_service.get_root_cause()
        assert root_cause == dns_service

    def test_get_root_cause_with_chain(self):
        """Test get_root_cause finds topmost failing parent in chain."""
        team = generate_sample_model_tree('Team', self.session)
        round_obj = generate_sample_model_tree('Round', self.session)

        network_service = Service(name="Network", team=team, check_name="ICMP Check", host='127.0.0.1')
        dns_service = Service(name="DNS", team=team, check_name="DNS Check", host='127.0.0.1')
        http_service = Service(name="HTTP", team=team, check_name="HTTP Check", host='127.0.0.1')
        self.session.add(network_service)
        self.session.add(dns_service)
        self.session.add(http_service)
        self.session.commit()

        dns_service.parent = network_service
        http_service.parent = dns_service

        # Network fails (root cause)
        check1 = Check(round=round_obj, service=network_service, result=False, output='Failed')
        self.session.add(check1)
        # DNS also fails
        check2 = Check(round=round_obj, service=dns_service, result=False, output='Failed')
        self.session.add(check2)
        self.session.commit()

        root_cause = http_service.get_root_cause()
        assert root_cause == network_service

    def test_get_dependency_chain(self):
        """Test get_dependency_chain returns all parent services."""
        team = generate_sample_model_tree('Team', self.session)

        network_service = Service(name="Network", team=team, check_name="ICMP Check", host='127.0.0.1')
        dns_service = Service(name="DNS", team=team, check_name="DNS Check", host='127.0.0.1')
        http_service = Service(name="HTTP", team=team, check_name="HTTP Check", host='127.0.0.1')
        self.session.add(network_service)
        self.session.add(dns_service)
        self.session.add(http_service)
        self.session.commit()

        dns_service.parent = network_service
        http_service.parent = dns_service
        self.session.commit()

        chain = http_service.get_dependency_chain()
        assert len(chain) == 2
        assert chain[0] == dns_service
        assert chain[1] == network_service

    def test_dependency_chain_prevents_circular(self):
        """Test that dependency chain traversal prevents infinite loops."""
        team = generate_sample_model_tree('Team', self.session)

        service_a = Service(name="Service A", team=team, check_name="Check A", host='127.0.0.1')
        service_b = Service(name="Service B", team=team, check_name="Check B", host='127.0.0.1')
        self.session.add(service_a)
        self.session.add(service_b)
        self.session.commit()

        # Create circular dependency (normally prevented by API, but test model safety)
        service_a.parent_id = service_b.id
        service_b.parent_id = service_a.id
        self.session.commit()

        # Should not hang - returns partial chain
        chain = service_a.get_dependency_chain()
        assert len(chain) <= 2  # Should stop at cycle

    def test_dependency_status_property(self):
        """Test dependency_status property returns correct info."""
        team = generate_sample_model_tree('Team', self.session)
        round_obj = generate_sample_model_tree('Round', self.session)

        dns_service = Service(name="DNS", team=team, check_name="DNS Check", host='127.0.0.1')
        http_service = Service(name="HTTP", team=team, check_name="HTTP Check", host='127.0.0.1')
        self.session.add(dns_service)
        self.session.add(http_service)
        self.session.commit()

        http_service.parent = dns_service
        # DNS fails
        check = Check(round=round_obj, service=dns_service, result=False, output='Failed')
        self.session.add(check)
        self.session.commit()

        status = http_service.dependency_status
        assert status["has_parent"] is True
        assert status["parent_id"] == dns_service.id
        assert status["parent_name"] == "DNS"
        assert status["parent_is_down"] is True
        assert status["root_cause"]["id"] == dns_service.id
        assert status["root_cause"]["name"] == "DNS"

    def test_children_relationship(self):
        """Test children backref returns all child services."""
        team = generate_sample_model_tree('Team', self.session)

        dns_service = Service(name="DNS", team=team, check_name="DNS Check", host='127.0.0.1')
        http_service = Service(name="HTTP", team=team, check_name="HTTP Check", host='127.0.0.1')
        smtp_service = Service(name="SMTP", team=team, check_name="SMTP Check", host='127.0.0.1')
        self.session.add(dns_service)
        self.session.add(http_service)
        self.session.add(smtp_service)
        self.session.commit()

        http_service.parent = dns_service
        smtp_service.parent = dns_service
        self.session.commit()

        assert len(dns_service.children) == 2
        assert http_service in dns_service.children
        assert smtp_service in dns_service.children
