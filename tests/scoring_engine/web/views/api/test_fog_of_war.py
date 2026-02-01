"""Tests for Fog of War functionality"""
import json

from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.web import create_app
from tests.scoring_engine.unit_test import UnitTest


class TestFogOfWar(UnitTest):
    """Tests for fog of war scoreboard hiding functionality"""

    def setup_method(self):
        super(TestFogOfWar, self).setup_method()
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

        # Create teams
        self.white_team = Team(name="White Team", color="White")
        self.blue_team = Team(name="Blue Team 1", color="Blue")
        self.blue_team2 = Team(name="Blue Team 2", color="Blue")
        self.red_team = Team(name="Red Team", color="Red")

        self.session.add_all(
            [self.white_team, self.blue_team, self.blue_team2, self.red_team]
        )
        self.session.commit()

        # Create users
        self.white_user = User(
            username="whiteuser", password="pass", team=self.white_team
        )
        self.blue_user = User(
            username="blueuser", password="pass", team=self.blue_team
        )
        self.red_user = User(username="reduser", password="pass", team=self.red_team)

        self.session.add_all([self.white_user, self.blue_user, self.red_user])
        self.session.commit()

        # Create fog of war setting (disabled by default)
        self.fog_setting = Setting(name="fog_of_war_enabled", value=False)
        self.overview_setting = Setting(name="overview_show_round_info", value=True)
        self.session.add_all([self.fog_setting, self.overview_setting])
        self.session.commit()

        # Create a round and some checks to generate scores
        self.round = Round(number=1)
        self.session.add(self.round)
        self.session.commit()

        # Create services for blue teams
        self.service1 = Service(
            name="HTTP",
            check_name="HTTPCheck",
            host="10.0.0.1",
            port=80,
            points=100,
            team=self.blue_team,
        )
        self.service2 = Service(
            name="HTTP",
            check_name="HTTPCheck",
            host="10.0.0.2",
            port=80,
            points=100,
            team=self.blue_team2,
        )
        self.session.add_all([self.service1, self.service2])
        self.session.commit()

        # Create successful checks to generate scores
        check1 = Check(round=self.round, service=self.service1)
        check1.finished(True, "Success", "OK", "ping")
        check2 = Check(round=self.round, service=self.service2)
        check2.finished(True, "Success", "OK", "ping")
        self.session.add_all([check1, check2])
        self.session.commit()

    def teardown_method(self):
        Setting.clear_cache()
        self.ctx.pop()
        super(TestFogOfWar, self).teardown_method()

    def login(self, username, password):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    def logout(self):
        return self.client.get("/logout", follow_redirects=True)

    def test_scoreboard_bar_data_visible_when_fog_disabled(self):
        """Scores should be visible when fog of war is disabled"""
        Setting.clear_cache()
        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        # Scores should be numeric, not "?"
        assert "?" not in data["service_scores"]
        assert "fog_of_war" not in data or data.get("fog_of_war") is False

    def test_scoreboard_bar_data_hidden_when_fog_enabled(self):
        """Scores should be hidden when fog of war is enabled for non-admin users"""
        # Enable fog of war
        self.fog_setting.value = True
        self.session.commit()
        Setting.clear_cache()

        # Anonymous user should see hidden scores
        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data.get("fog_of_war") is True
        assert all(score == "?" for score in data["service_scores"])

    def test_scoreboard_bar_data_visible_for_white_team_when_fog_enabled(self):
        """White team should always see scores even when fog of war is enabled"""
        # Enable fog of war
        self.fog_setting.value = True
        self.session.commit()
        Setting.clear_cache()

        # Login as white team
        self.login("whiteuser", "pass")

        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        # White team should see actual scores
        assert "fog_of_war" not in data or data.get("fog_of_war") is False
        assert "?" not in data["service_scores"]

    def test_scoreboard_line_data_hidden_when_fog_enabled(self):
        """Line chart data should be empty when fog of war is enabled"""
        # Enable fog of war
        self.fog_setting.value = True
        self.session.commit()
        Setting.clear_cache()

        resp = self.client.get("/api/scoreboard/get_line_data")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data.get("fog_of_war") is True
        # Scores should be empty arrays
        for team in data["team"]:
            assert team["scores"] == []

    def test_overview_data_scores_hidden_when_fog_enabled(self):
        """Overview should hide scores but show service status when fog enabled"""
        # Enable fog of war
        self.fog_setting.value = True
        self.session.commit()
        Setting.clear_cache()

        resp = self.client.get("/api/overview/get_data")
        assert resp.status_code == 200
        data = json.loads(resp.data)

        # First row is "Current Score" - values should be "?"
        scores_row = data["data"][0]
        assert scores_row[0] == "Current Score"
        for score in scores_row[1:]:
            assert score == "?"

        # Second row is "Current Place" - values should be "?"
        places_row = data["data"][1]
        assert places_row[0] == "Current Place"
        for place in places_row[1:]:
            assert place == "?"

    def test_fog_of_war_toggle_requires_white_team(self):
        """Only white team should be able to toggle fog of war"""
        Setting.clear_cache()

        # Try as blue team - should fail
        self.login("blueuser", "pass")
        resp = self.client.post("/api/admin/update_fog_of_war")
        assert resp.status_code == 403
        self.logout()

        # Try as white team - should succeed
        self.login("whiteuser", "pass")
        resp = self.client.post(
            "/api/admin/update_fog_of_war", follow_redirects=False
        )
        # Should redirect to permissions page on success
        assert resp.status_code == 302
        assert "permissions" in resp.location
