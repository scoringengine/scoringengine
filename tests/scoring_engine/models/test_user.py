from scoring_engine.models.user import User
from scoring_engine.models.team import Team

from sqlalchemy.exc import IntegrityError

import pytest
from tests.scoring_engine.helpers import generate_sample_model_tree
from tests.scoring_engine.unit_test import UnitTest


class TestUser(UnitTest):
    def test_init_service(self):
        user = User(username="testuser", password="testpass")
        assert user.id is None
        assert user.username == "testuser"
        assert user.check_password("testpass")
        assert type(user.password) is str
        assert user.team is None
        assert user.team_id is None
        assert user.is_authenticated is None
        assert user.is_active is True
        assert user.is_anonymous is False
        assert user.get_username == "testuser"
        assert user.get_id() is None

    def test_basic_user(self):
        team = generate_sample_model_tree("Team", self.session)
        user = User(username="testuser", password="testpass", team=team)
        self.session.add(user)
        self.session.commit()
        assert user.id == 1
        assert user.username == "testuser"
        assert user.check_password("testpass")
        assert user.team is team
        assert user.team_id is team.id
        assert user.get_id() == 1

    def test_username_unique(self):
        team = generate_sample_model_tree("Team", self.session)
        user1 = User(username="testuser", password="testpass", team=team)
        self.session.add(user1)
        self.session.commit()
        with pytest.raises(IntegrityError):
            user2 = User(username="testuser", password="testpass", team=team)
            self.session.add(user2)
            self.session.commit()

    def test_red_team_user(self):
        team = Team(name="Red Team", color="Red")
        self.session.add(team)
        self.session.commit()
        user = User(username="testuser", password="testpass", team=team)
        self.session.add(user)
        self.session.commit()
        user.is_red_team is True
        user.is_white_team is False
        user.is_blue_team is False

    def test_white_team_user(self):
        team = Team(name="White Team", color="White")
        self.session.add(team)
        self.session.commit()
        user = User(username="testuser", password="testpass", team=team)
        self.session.add(user)
        self.session.commit()
        user.is_red_team is False
        user.is_white_team is True
        user.is_blue_team is False

    def test_blue_team_user(self):
        team = Team(name="Blue Team", color="Blue")
        self.session.add(team)
        self.session.commit()
        user = User(username="testuser", password="testpass", team=team)
        self.session.add(user)
        self.session.commit()
        user.is_red_team is False
        user.is_white_team is False
        user.is_blue_team is True
