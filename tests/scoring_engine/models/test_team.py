import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.models.service import Service

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from helpers import generate_sample_model_tree
from unit_test import UnitTest


class TestTeam(UnitTest):

    def test_init_whiteteam(self):
        team = Team(name="White Team", color="White")
        assert team.name == "White Team"
        assert team.color == "White"
        assert team.id is None
        assert team.current_score() == 2000
        assert team.is_red_team is False
        assert team.is_white_team is True
        assert team.is_blue_team is False

    def test_init_blueteam(self):
        team = Team(name="Blue Team", color="Blue")
        assert team.name == "Blue Team"
        assert team.color == "Blue"
        assert team.id is None
        assert team.current_score() == 2000
        assert team.is_red_team is False
        assert team.is_white_team is False
        assert team.is_blue_team is True

    def test_init_redteam(self):
        team = Team(name="Red Team", color="Red")
        assert team.name == "Red Team"
        assert team.color == "Red"
        assert team.id is None
        assert team.current_score() == 2000
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
        service_1 = Service(name="Example Service 1", team=team, check_name="ICMP IPv4 Check")
        service_2 = Service(name="Example Service 2", team=team, check_name="SSH IPv4 Check")
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
