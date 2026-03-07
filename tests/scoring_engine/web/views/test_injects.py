"""Tests for Injects web view"""

from datetime import datetime, timedelta, timezone

import pytest

from scoring_engine.db import db
from scoring_engine.models.inject import Inject, Template
from scoring_engine.models.team import Team
from scoring_engine.models.user import User


class TestInjects:
    """Test injects web view authorization and rendering"""

    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session):
        self.client = test_client
        self.white_team = Team(name="White Team", color="White")
        self.red_team = Team(name="Red Team", color="Red")
        self.blue_team = Team(name="Blue Team", color="Blue")

        db.session.add_all([self.white_team, self.red_team, self.blue_team])
        db.session.commit()

        self.white_user = User(username="whiteuser", password="testpass", team=self.white_team)
        self.red_user = User(username="reduser", password="testpass", team=self.red_team)
        self.blue_user = User(username="blueuser", password="testpass", team=self.blue_team)

        db.session.add_all([self.white_user, self.red_user, self.blue_user])
        db.session.commit()

    def login(self, username):
        return self.client.post(
            "/login",
            data={"username": username, "password": "testpass"},
            follow_redirects=True,
        )

    def test_injects_requires_auth(self):
        resp = self.client.get("/injects")
        assert resp.status_code == 302
        assert "/login?" in resp.location

    def test_injects_blue_team_authorized(self):
        self.login("blueuser")
        resp = self.client.get("/injects")
        assert resp.status_code == 200

    def test_injects_red_team_authorized(self):
        self.login("reduser")
        resp = self.client.get("/injects")
        assert resp.status_code == 200

    def test_injects_white_team_unauthorized(self):
        self.login("whiteuser")
        resp = self.client.get("/injects")
        assert resp.status_code == 302
        assert "/unauthorized" in resp.location

    def test_inject_detail_requires_auth(self):
        resp = self.client.get("/inject/1")
        assert resp.status_code == 302

    def test_inject_detail_team_authorization(self):
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        inject = Inject(team=self.blue_team, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        self.login("reduser")
        resp = self.client.get(f"/inject/{inject.id}")
        assert resp.status_code == 302
        assert "/unauthorized" in resp.location

    def test_inject_detail_before_start_time(self):
        template = Template(
            title="Future Inject",
            scenario="Test",
            deliverable="Test",
            start_time=datetime.now(timezone.utc) + timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=2),
        )
        inject = Inject(team=self.blue_team, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        self.login("blueuser")
        resp = self.client.get(f"/inject/{inject.id}")
        assert resp.status_code == 302
        assert "/unauthorized" in resp.location

    def test_inject_detail_authorized(self):
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        inject = Inject(team=self.blue_team, template=template)
        db.session.add_all([template, inject])
        db.session.commit()

        self.login("blueuser")
        resp = self.client.get(f"/inject/{inject.id}")
        assert resp.status_code == 200
