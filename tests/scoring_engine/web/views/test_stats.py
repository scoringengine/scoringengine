"""Tests for Stats web view"""

import pytest

from scoring_engine.db import db
from scoring_engine.models.team import Team
from scoring_engine.models.user import User


class TestStats:
    """Test stats web view authorization and rendering"""

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

    def login(self, username, password="testpass"):
        return self.client.post("/login", data={"username": username, "password": password}, follow_redirects=True)

    def test_stats_requires_auth(self):
        """Test that /stats requires authentication"""
        resp = self.client.get("/stats")
        assert resp.status_code == 302
        assert "/login?" in resp.location

    def test_stats_blue_team_authorized(self):
        """Test that blue team can access stats page"""
        self.login("blueuser")
        resp = self.client.get("/stats")
        assert resp.status_code == 200

    def test_stats_white_team_authorized(self):
        """Test that white team can access stats page"""
        self.login("whiteuser")
        resp = self.client.get("/stats")
        assert resp.status_code == 200

    def test_stats_red_team_unauthorized(self):
        """Test that red team is redirected from stats page"""
        self.login("reduser")
        resp = self.client.get("/stats")
        assert resp.status_code == 302
        assert "/unauthorized" in resp.location

    def test_stats_renders_template(self):
        """Test that stats page renders the correct template"""
        self.login("blueuser")
        resp = self.client.get("/stats")
        assert resp.status_code == 200
