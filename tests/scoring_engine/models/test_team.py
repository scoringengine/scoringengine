import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.models.service import Service
from scoring_engine.models.check import Check

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from helpers import generate_sample_model_tree
from unit_test import UnitTest


class TestTeam(UnitTest):

    def test_init_whiteteam(self):
        team = Team(name="White Team", color="White")
        assert team.name == "White Team"
        assert team.color == "White"
        assert team.id is None
        assert team.current_score == 0
        assert team.is_red_team is False
        assert team.is_white_team is True
        assert team.is_blue_team is False

    def test_init_blueteam(self):
        team = Team(name="Blue Team", color="Blue")
        assert team.name == "Blue Team"
        assert team.color == "Blue"
        assert team.id is None
        assert team.current_score == 0
        assert team.is_red_team is False
        assert team.is_white_team is False
        assert team.is_blue_team is True

    def test_init_redteam(self):
        team = Team(name="Red Team", color="Red")
        assert team.name == "Red Team"
        assert team.color == "Red"
        assert team.id is None
        assert team.current_score == 0
        assert team.is_red_team is True
        assert team.is_white_team is False
        assert team.is_blue_team is False

    def test_simple_save(self):
        white_team = Team(name="White Team", color="White")
        self.db.save(white_team)
        assert white_team.id is not None
        assert len(self.db.session.query(Team).all()) == 1

    def test_multiple_saves(self):
        white_team = Team(name="White Team", color="White")
        self.db.save(white_team)
        blue_team = Team(name="Blue", color="Blue")
        self.db.save(blue_team)
        assert len(self.db.session.query(Team).all()) == 2

    def test_services(self):
        team = generate_sample_model_tree('Team', self.db)
        service_1 = Service(name="Example Service 1", team=team, check_name="ICMP IPv4 Check", ip_address='127.0.0.1')
        service_2 = Service(name="Example Service 2", team=team, check_name="SSH IPv4 Check", ip_address='2.3.4.5')
        self.db.save(service_1)
        self.db.save(service_2)
        assert team.services == [service_1, service_2]

    def test_users(self):
        team = generate_sample_model_tree('Team', self.db)
        user_1 = User(username="testuser", password="testpass", team=team)
        user_2 = User(username="abcuser", password="abcpass", team=team)
        self.db.save(user_1)
        self.db.save(user_2)
        assert team.users == [user_1, user_2]

    def test_current_score(self):
        team = generate_sample_model_tree('Team', self.db)
        service_1 = Service(name="Example Service 1", team=team, check_name="ICMP IPv4 Check", ip_address='127.0.0.1')
        self.db.save(service_1)
        check_1 = Check(service=service_1, result=True, output='Good output')
        self.db.save(check_1)
        service_2 = Service(name="Example Service 2", team=team, check_name="SSH IPv4 Check", ip_address='127.0.0.2')
        self.db.save(service_2)
        check_2 = Check(service=service_2, result=True, output='Good output')
        self.db.save(check_2)
        check_3 = Check(service=service_2, result=True, output='Good output')
        self.db.save(check_3)
        service_3 = Service(name="Example Service 3", team=team, check_name="SSH IPv4 Check", ip_address='127.0.0.3')
        self.db.save(service_3)
        check_3 = Check(service=service_3, result=False, output='bad output')
        self.db.save(check_3)
        assert team.current_score == 300

    def test_place(self):
        team_1 = Team(name="Blue Team 1", color="Blue")
        self.db.save(team_1)
        service_1 = Service(name="Example Service 1", team=team_1, check_name="ICMP IPv4 Check", ip_address='127.0.0.1')
        self.db.save(service_1)
        check_1 = Check(service=service_1, result=True, output='Good output')
        check_2 = Check(service=service_1, result=True, output='Good output')
        self.db.save(check_1)
        self.db.save(check_2)

        team_2 = Team(name="Blue Team 2", color="Blue")
        self.db.save(team_2)
        service_1 = Service(name="Example Service 1", team=team_2, check_name="ICMP IPv4 Check", ip_address='127.0.0.1')
        self.db.save(service_1)
        check_1 = Check(service=service_1, result=False, output='Good output')
        check_2 = Check(service=service_1, result=False, output='Good output')
        self.db.save(check_1)
        self.db.save(check_2)

        team_3 = Team(name="Blue Team 3", color="Blue")
        self.db.save(team_3)
        service_1 = Service(name="Example Service 1", team=team_3, check_name="ICMP IPv4 Check", ip_address='127.0.0.1')
        self.db.save(service_1)
        check_1 = Check(service=service_1, result=True, output='Good output')
        check_2 = Check(service=service_1, result=False, output='Good output')
        self.db.save(check_1)
        self.db.save(check_2)
        assert team_1.place == 1
        assert team_2.place == 3
        assert team_3.place == 2
