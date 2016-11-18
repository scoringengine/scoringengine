import pytest

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.models.user import User
from scoring_engine.models.team import Team

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from helpers import generate_sample_model_tree
from unit_test import UnitTest

from sqlalchemy.exc import IntegrityError



class TestUser(UnitTest):

    def test_init_service(self):
        user = User(username="testuser", password="testpass")
        assert user.id is None
        assert user.username == "testuser"
        assert user.password == User.generate_hash('testpass')
        assert type(user.password) is str
        assert user.team is None
        assert user.team_id is None
        assert user.is_authenticated is None
        assert user.is_active is True
        assert user.is_anonymous is False
        assert user.get_username == 'testuser'
        assert user.get_id() is None

    def test_basic_user(self):
        team = generate_sample_model_tree('Team', self.db)
        user = User(username="testuser", password="testpass", team=team)
        self.db.save(user)
        assert user.id is 1
        assert user.username == "testuser"
        assert user.password == User.generate_hash('testpass')
        assert user.team is team
        assert user.team_id is team.id
        assert user.get_id() == 1

    def test_username_unique(self):
        team = generate_sample_model_tree('Team', self.db)
        user1 = User(username="testuser", password="testpass", team=team)
        self.db.save(user1)
        with pytest.raises(IntegrityError):
            user2 = User(username="testuser", password="testpass", team=team)
            self.db.save(user2)

    def test_red_team_user(self):
        team = Team(name="Red Team", color="Red")
        self.db.save(team)
        user = User(username='testuser', password='testpass', team=team)
        self.db.save(user)
        user.is_red_team is True
        user.is_white_team is False
        user.is_blue_team is False

    def test_white_team_user(self):
        team = Team(name="White Team", color="White")
        self.db.save(team)
        user = User(username='testuser', password='testpass', team=team)
        self.db.save(user)
        user.is_red_team is False
        user.is_white_team is True
        user.is_blue_team is False

    def test_blue_team_user(self):
        team = Team(name="Blue Team", color="Blue")
        self.db.save(team)
        user = User(username='testuser', password='testpass', team=team)
        self.db.save(user)
        user.is_red_team is False
        user.is_white_team is False
        user.is_blue_team is True
