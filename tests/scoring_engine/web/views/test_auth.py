import mock
import pytest

from scoring_engine.db import db
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.web.views.auth import LoginForm


class TestAuth:

    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session):
        self.client = test_client

    def _create_default_user(self):
        team = Team(name="Team 1", color="White")
        db.session.add(team)
        user = User(username="testuser", password="testpass", team=team)
        db.session.add(user)
        db.session.commit()
        return user

    def _auth_and_get_path(self, path):
        self.client.post("/login", data={"username": "testuser", "password": "testpass"})
        return self.client.get(path)

    def test_login_page_auth_required(self):
        resp = self.client.get("/login")
        assert resp.status_code == 200

    def test_unauthorized(self):
        resp = self.client.get("/unauthorized")
        assert resp.status_code == 200

    def test_auth_required_logout(self):
        resp = self.client.get("/logout")
        assert resp.status_code == 302
        assert "/login?" in resp.location

    @pytest.mark.parametrize("color", ["White", "Blue", "Red"], ids=["white", "blue", "red"])
    def test_login_logout(self, color):
        user = self._create_default_user()
        user.team.color = color
        db.session.add(user.team)
        db.session.commit()
        assert user.authenticated is False
        self._auth_and_get_path("/")
        assert user.authenticated is True
        logout_resp = self.client.get("/logout")
        assert user.authenticated is False
        assert logout_resp.status_code == 302
        resp = self.client.get("/services")
        assert resp.status_code == 302
        assert "/login?" in resp.location

    def test_wrong_username_login(self):
        user = self._create_default_user()
        user.username = "RandomName"
        db.session.add(user)
        db.session.commit()
        self._auth_and_get_path("/")
        assert user.authenticated is False

    def test_wrong_password_login(self):
        user = self._create_default_user()
        user.update_password("randompass")
        db.session.add(user)
        db.session.commit()
        self._auth_and_get_path("/")
        assert user.authenticated is False

    def test_form_errors(self):
        with mock.patch.object(LoginForm, "errors") as mock_fish:
            mock_fish.__get__ = mock.Mock(return_value="Some error text")
            self.client.get("/login")

    def test_login_twice(self):
        self._create_default_user()
        self._auth_and_get_path("/")
        self._auth_and_get_path("/")
