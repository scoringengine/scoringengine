from datetime import datetime, timedelta, timezone

import pytest

from scoring_engine.db import db
from scoring_engine.models.check import Check
from scoring_engine.models.inject import Inject, Template
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.models.user import User

ADMIN_PATHS = [
    "/admin",
    "/admin/status",
    "/admin/workers",
    "/admin/queues",
    "/admin/manage",
    "/admin/permissions",
    "/admin/settings",
    "/admin/injects/templates",
    "/admin/injects/scores",
    "/admin/announcements",
    "/admin/welcome",
    "/admin/sla",
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

    def test_inject_detail_auth_and_access(self):
        blue_team = Team(name="Blue Team", color="Blue")
        db.session.add(blue_team)
        db.session.flush()
        template = Template(
            title="Test",
            scenario="Test scenario",
            deliverable="Test deliverable",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
        )
        db.session.add(template)
        db.session.flush()
        inject = Inject(team=blue_team, template=template)
        db.session.add(inject)
        db.session.commit()

        # Requires auth
        resp = self.client.get(f"/admin/injects/{inject.id}")
        assert resp.status_code == 302
        assert "/login?" in resp.location

        # White team can access
        resp = self._auth_and_get_path(f"/admin/injects/{inject.id}")
        assert resp.status_code == 200

    def test_inject_detail_unauthorized_non_white(self):
        red_team = Team(name="Red Team", color="Red")
        db.session.add(red_team)
        user = User(username="testuser_red2", password="testpass_red", team=red_team)
        db.session.add(user)
        db.session.commit()
        self.client.post("/login", data={"username": "testuser_red2", "password": "testpass_red"})
        resp = self.client.get("/admin/injects/1")
        assert resp.status_code == 302
        assert "unauthorized" in str(resp.data)

    def test_template_submissions_auth_and_access(self):
        # Requires auth
        resp = self.client.get("/admin/injects/template/1/submissions")
        assert resp.status_code == 302
        assert "/login?" in resp.location

        # White team can access
        resp = self._auth_and_get_path("/admin/injects/template/1/submissions")
        assert resp.status_code == 200

    def test_template_submissions_unauthorized_non_white(self):
        red_team = Team(name="Red Team", color="Red")
        db.session.add(red_team)
        user = User(username="testuser_red3", password="testpass_red", team=red_team)
        db.session.add(user)
        db.session.commit()
        self.client.post("/login", data={"username": "testuser_red3", "password": "testpass_red"})
        resp = self.client.get("/admin/injects/template/1/submissions")
        assert resp.status_code == 302
        assert "unauthorized" in str(resp.data)


class TestAdminCheckRedirect:
    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session):
        self.client = test_client
        self.white_team = Team(name="White Team", color="White")
        self.blue_team = Team(name="Blue Team", color="Blue")
        db.session.add_all([self.white_team, self.blue_team])
        db.session.commit()

        self.white_user = User(username="whiteuser", password="testpass", team=self.white_team)
        db.session.add(self.white_user)

        self.service = Service(name="SSH", check_name="SSH Check", host="10.0.0.1", team=self.blue_team)
        db.session.add(self.service)
        db.session.commit()

        now = datetime.now(timezone.utc)
        self.round = Round(number=1, round_start=now - timedelta(seconds=60), round_end=now)
        db.session.add(self.round)
        db.session.flush()

        self.check = Check(service=self.service, round=self.round, result=True, output="ok", completed=True)
        db.session.add(self.check)
        db.session.commit()

    def _login_white(self):
        self.client.post("/login", data={"username": "whiteuser", "password": "testpass"})

    def test_check_redirect_requires_auth(self):
        resp = self.client.get(f"/admin/check/{self.check.id}")
        assert resp.status_code == 302
        assert "/login?" in resp.location

    def test_check_redirect_white_team(self):
        self._login_white()
        resp = self.client.get(f"/admin/check/{self.check.id}")
        assert resp.status_code == 302
        assert f"/admin/service/{self.service.id}#check-{self.check.id}" in resp.location

    def test_check_redirect_nonexistent(self):
        self._login_white()
        resp = self.client.get("/admin/check/99999")
        assert resp.status_code == 302
        assert "/admin" in resp.location

    def test_check_redirect_unauthorized_non_white(self):
        red_team = Team(name="Red Team", color="Red")
        db.session.add(red_team)
        red_user = User(username="reduser", password="testpass", team=red_team)
        db.session.add(red_user)
        db.session.commit()
        self.client.post("/login", data={"username": "reduser", "password": "testpass"})
        resp = self.client.get(f"/admin/check/{self.check.id}")
        assert resp.status_code == 302
        assert "unauthorized" in str(resp.data)
