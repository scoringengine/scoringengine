"""Tests for Injects web view"""

from datetime import datetime, timedelta, timezone

from scoring_engine.models.inject import Inject, Template
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from tests.scoring_engine.web.web_test import WebTest


class TestInjects(WebTest):
    """Test injects web view authorization and rendering"""

    def setup_method(self):
        super(TestInjects, self).setup_method()
        self.white_team = Team(name="White Team", color="White")
        self.red_team = Team(name="Red Team", color="Red")
        self.blue_team = Team(name="Blue Team", color="Blue")

        self.session.add_all([self.white_team, self.red_team, self.blue_team])
        self.session.commit()

        self.white_user = User(username="whiteuser", password="pass", team=self.white_team)
        self.red_user = User(username="reduser", password="pass", team=self.red_team)
        self.blue_user = User(username="blueuser", password="pass", team=self.blue_team)

        self.session.add_all([self.white_user, self.red_user, self.blue_user])
        self.session.commit()

    def test_injects_requires_auth(self):
        resp = self.client.get("/injects")
        assert resp.status_code == 302
        assert "/login?" in resp.location

    def test_injects_blue_team_authorized(self):
        self.login("blueuser", "pass")
        resp = self.client.get("/injects")
        assert resp.status_code == 200

    def test_injects_red_team_authorized(self):
        self.login("reduser", "pass")
        resp = self.client.get("/injects")
        assert resp.status_code == 200

    def test_injects_white_team_unauthorized(self):
        self.login("whiteuser", "pass")
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
        self.session.add_all([template, inject])
        self.session.commit()

        self.login("reduser", "pass")
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
        self.session.add_all([template, inject])
        self.session.commit()

        self.login("blueuser", "pass")
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
        self.session.add_all([template, inject])
        self.session.commit()

        self.login("blueuser", "pass")
        resp = self.client.get(f"/inject/{inject.id}")
        assert resp.status_code == 200
