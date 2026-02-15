import pytest

from scoring_engine.db import db
from scoring_engine.models.team import Team
from scoring_engine.models.user import User


class TestProfile:

    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session):
        self.client = test_client

    def login(self, username, password="testpass"):
        return self.client.post("/login", data={"username": username, "password": password}, follow_redirects=True)

    def _create_default_user(self):
        team = Team(name="Team 1", color="White")
        db.session.add(team)
        user = User(username="testuser", password="testpass", team=team)
        db.session.add(user)
        db.session.commit()
        return user

    def test_home_auth_required(self):
        resp = self.client.get("/profile")
        assert resp.status_code == 302
        assert "/login?" in resp.location

    def test_home_with_auth(self):
        self._create_default_user()
        self.login("testuser")
        resp = self.client.get("/profile")
        assert resp.status_code == 200
