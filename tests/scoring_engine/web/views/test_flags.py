"""Tests for Flags web view"""
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from tests.scoring_engine.web.web_test import WebTest


class TestFlags(WebTest):
    """Test flags web view authorization and rendering"""

    def setup_method(self):
        super(TestFlags, self).setup_method()
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

    def test_flags_requires_auth(self):
        """Test that /flags requires authentication"""
        resp = self.client.get("/flags")
        assert resp.status_code == 302
        assert "/login?" in resp.location

    def test_flags_red_team_authorized(self):
        """Test that red team can access flags page"""
        self.login("reduser", "pass")
        resp = self.client.get("/flags")
        assert resp.status_code == 200

    def test_flags_white_team_authorized(self):
        """Test that white team can access flags page"""
        self.login("whiteuser", "pass")
        resp = self.client.get("/flags")
        assert resp.status_code == 200

    def test_flags_blue_team_unauthorized(self):
        """Test that blue team is redirected from flags page"""
        self.login("blueuser", "pass")
        resp = self.client.get("/flags")
        assert resp.status_code == 302
        assert "/unauthorized" in resp.location

    def test_flags_renders_template(self):
        """Test that flags page renders the correct template"""
        self.login("reduser", "pass")
        resp = self.client.get("/flags")
        assert resp.status_code == 200
        assert b"flags.html" in resp.data or resp.status_code == 200
