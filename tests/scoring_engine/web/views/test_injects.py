"""Tests for Injects web view"""
from datetime import datetime, timedelta

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
        """Test that /injects requires authentication"""
        resp = self.client.get("/injects")
        assert resp.status_code == 302
        assert "/login?" in resp.location

    def test_injects_blue_team_authorized(self):
        """Test that blue team can access injects page"""
        self.login("blueuser", "pass")
        resp = self.client.get("/injects")
        assert resp.status_code == 200

    def test_injects_red_team_authorized(self):
        """Test that red team can access injects page"""
        self.login("reduser", "pass")
        resp = self.client.get("/injects")
        assert resp.status_code == 200

    def test_injects_white_team_unauthorized(self):
        """Test that white team is redirected from injects page"""
        self.login("whiteuser", "pass")
        resp = self.client.get("/injects")
        assert resp.status_code == 302
        assert "/unauthorized" in resp.location

    def test_inject_detail_requires_auth(self):
        """Test that inject detail page requires authentication"""
        resp = self.client.get("/inject/1")
        assert resp.status_code == 302

    def test_inject_detail_team_authorization(self):
        """Test that users can only view their own team's injects"""
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow() + timedelta(hours=1)
        )
        inject = Inject(team=self.blue_team, template=template)
        self.session.add_all([template, inject])
        self.session.commit()

        # Try to access as red team
        self.login("reduser", "pass")
        resp = self.client.get(f"/inject/{inject.id}")
        assert resp.status_code == 302
        assert "/unauthorized" in resp.location

    def test_inject_detail_before_start_time(self):
        """Test that inject cannot be viewed before start time"""
        template = Template(
            title="Future Inject",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.utcnow() + timedelta(hours=1),
            end_time=datetime.utcnow() + timedelta(hours=2)
        )
        inject = Inject(team=self.blue_team, template=template)
        self.session.add_all([template, inject])
        self.session.commit()

        self.login("blueuser", "pass")
        resp = self.client.get(f"/inject/{inject.id}")
        assert resp.status_code == 302
        assert "/unauthorized" in resp.location

    def test_inject_detail_authorized(self):
        """Test that team can view their inject after start time"""
        template = Template(
            title="Test",
            scenario="Test",
            deliverable="Test",
            score=10,
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow() + timedelta(hours=1)
        )
        inject = Inject(team=self.blue_team, template=template)
        self.session.add_all([template, inject])
        self.session.commit()

        self.login("blueuser", "pass")
        resp = self.client.get(f"/inject/{inject.id}")
        assert resp.status_code == 200
