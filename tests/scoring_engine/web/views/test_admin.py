import pytest

from scoring_engine.db import db
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.models.user import User

ADMIN_PATHS = [
    "/admin",
    "/admin/status",
    "/admin/workers",
    "/admin/queues",
    "/admin/webserver",
    "/admin/manage",
    "/admin/permissions",
    "/admin/settings",
]


class TestAdmin:

    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session):
        self.client = test_client
        team = Team(name="Team 1", color="White")
        db.session.add(team)
        user = User(username="testuser", password="testpass", team=team)
        db.session.add(user)
        db.session.commit()

        service = Service(name="Example Service", check_name="ICMP IPv4 Check", host="127.0.0.1", team=team)
        db.session.add(service)
        db.session.commit()

    def _auth_and_get_path(self, path):
        self.client.post("/login", data={"username": "testuser", "password": "testpass"})
        return self.client.get(path)

    @pytest.mark.parametrize("path", ADMIN_PATHS)
    def test_auth_required(self, path):
        resp = self.client.get(path)
        assert resp.status_code == 302
        assert "/login?" in resp.location
        resp = self._auth_and_get_path(path)
        assert resp.status_code == 200

    @pytest.mark.parametrize("path", ADMIN_PATHS[1:])  # /admin itself doesn't have unauthorized test
    def test_unauthorized(self, path):
        red_team = Team(name="Red Team", color="Red")
        db.session.add(red_team)
        user = User(username="testuser_red", password="testpass_red", team=red_team)
        db.session.add(user)
        db.session.commit()
        self.client.post("/login", data={"username": "testuser_red", "password": "testpass_red"})
        resp = self.client.get(path)
        assert resp.status_code == 302
        assert "unauthorized" in str(resp.data)

    def test_auth_required_admin_service(self):
        resp = self.client.get("/admin/service/1")
        assert resp.status_code == 302
        assert "/login?" in resp.location
        resp = self._auth_and_get_path("/admin/service/1")
        assert resp.status_code == 200

    def test_admin_bad_service(self):
        resp = self.client.get("/admin/service/200")
        assert resp.status_code == 302
        assert "/login?" in resp.location
        resp = self._auth_and_get_path("/admin/service/200")
        assert resp.status_code == 302
        assert "unauthorized" in str(resp.data)

    def test_auth_bad_auth_team(self):
        red_team = Team(name="Red Team", color="Red")
        db.session.add(red_team)
        user = User(username="testuser_red", password="testpass_red", team=red_team)
        db.session.add(user)
        db.session.commit()
        self.client.post("/login", data={"username": "testuser_red", "password": "testpass_red"})
        resp = self.client.get("/admin/service/3")
        assert resp.status_code == 302
        assert "unauthorized" in str(resp.data)
