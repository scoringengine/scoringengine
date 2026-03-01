"""Tests for Weighted Scoring functionality"""
import json
from datetime import datetime, timedelta

from scoring_engine.models.check import Check
from scoring_engine.models.inject import Inject, Template
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.web import create_app
from tests.scoring_engine.unit_test import UnitTest


class TestWeightedScoring(UnitTest):
    """Tests for weighted scoring functionality"""

    def setup_method(self):
        super(TestWeightedScoring, self).setup_method()
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

        self.session.add_all([self.white_team, self.blue_team, self.blue_team2])
        self.session.commit()

        # Create users
        self.white_user = User(
            username="whiteuser", password="pass", team=self.white_team
        )
        self.blue_user = User(
            username="blueuser", password="pass", team=self.blue_team
        )

        self.session.add_all([self.white_user, self.blue_user])
        self.session.commit()

        # Create weighted scoring settings (disabled by default)
        self.session.add(Setting(name="weighted_scoring_enabled", value=False))
        self.session.add(Setting(name="service_weight", value="1.0"))
        self.session.add(Setting(name="inject_weight", value="1.0"))
        self.session.add(Setting(name="flag_weight", value="1.0"))
        self.session.commit()

        # Create a round and some checks to generate scores
        self.round = Round(number=1)
        self.session.add(self.round)
        self.session.commit()

        # Create services for blue teams - 100 points each
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

        # Create inject template and inject for blue_team - 50 points
        self.template = Template(
            title="Test Inject",
            scenario="Test scenario",
            deliverable="Test deliverable",
            score=50,
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=1),
        )
        self.session.add(self.template)
        self.session.commit()

        self.inject = Inject(team=self.blue_team, template=self.template)
        self.inject.score = 50
        self.inject.status = "Graded"
        self.session.add(self.inject)
        self.session.commit()

    def teardown_method(self):
        Setting.clear_cache()
        self.ctx.pop()
        super(TestWeightedScoring, self).teardown_method()

    def login(self, username, password):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    def logout(self):
        return self.client.get("/logout", follow_redirects=True)

    def test_scores_unweighted_by_default(self):
        """Scores should not be weighted when weighted scoring is disabled"""
        Setting.clear_cache()
        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = json.loads(resp.data)

        # Blue Team 1 has 100 service + 50 inject = 150
        assert data["service_scores"][0] == "100"
        assert data["inject_scores"][0] == "50"
        assert data["adjusted_scores"][0] == "150"
        assert data["weighted_scoring_enabled"] is False

    def test_weighted_service_scores(self):
        """Service scores should be multiplied by service_weight"""
        # Enable weighted scoring with 0.5 service weight
        setting = Setting.get_setting("weighted_scoring_enabled")
        setting.value = True
        self.session.commit()

        weight_setting = Setting.get_setting("service_weight")
        weight_setting.value = "0.5"
        self.session.commit()
        Setting.clear_cache()

        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = json.loads(resp.data)

        # Blue Team 1: 100 * 0.5 = 50 service + 50 inject = 100 total
        assert data["service_scores"][0] == "50"
        assert data["inject_scores"][0] == "50"
        assert data["adjusted_scores"][0] == "100"
        assert data["weighted_scoring_enabled"] is True

    def test_weighted_inject_scores(self):
        """Inject scores should be multiplied by inject_weight"""
        # Enable weighted scoring with 2.0 inject weight
        setting = Setting.get_setting("weighted_scoring_enabled")
        setting.value = True
        self.session.commit()

        weight_setting = Setting.get_setting("inject_weight")
        weight_setting.value = "2.0"
        self.session.commit()
        Setting.clear_cache()

        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = json.loads(resp.data)

        # Blue Team 1: 100 service + (50 * 2.0) = 100 inject = 200 total
        assert data["service_scores"][0] == "100"
        assert data["inject_scores"][0] == "100"
        assert data["adjusted_scores"][0] == "200"

    def test_combined_weights(self):
        """Both service and inject weights should apply"""
        # Enable weighted scoring with both weights
        setting = Setting.get_setting("weighted_scoring_enabled")
        setting.value = True
        self.session.commit()

        service_weight = Setting.get_setting("service_weight")
        service_weight.value = "0.1"  # 100 * 0.1 = 10
        inject_weight = Setting.get_setting("inject_weight")
        inject_weight.value = "10.0"  # 50 * 10 = 500
        self.session.commit()
        Setting.clear_cache()

        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = json.loads(resp.data)

        # Blue Team 1: (100 * 0.1) + (50 * 10) = 10 + 500 = 510
        assert data["service_scores"][0] == "10"
        assert data["inject_scores"][0] == "500"
        assert data["adjusted_scores"][0] == "510"

    def test_admin_get_weighted_scoring_settings(self):
        """White team should be able to get weighted scoring settings"""
        self.login("whiteuser", "pass")
        resp = self.client.get("/api/admin/weighted_scoring/settings")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "enabled" in data
        assert "service_weight" in data
        assert "inject_weight" in data
        assert "flag_weight" in data

    def test_admin_update_weighted_scoring_settings(self):
        """White team should be able to update weighted scoring settings"""
        self.login("whiteuser", "pass")
        resp = self.client.post(
            "/api/admin/weighted_scoring/settings",
            data=json.dumps({
                "enabled": True,
                "service_weight": 0.5,
                "inject_weight": 2.0,
                "flag_weight": 1.5,
            }),
            content_type="application/json",
        )
        assert resp.status_code == 200
        Setting.clear_cache()

        # Verify settings were saved
        resp = self.client.get("/api/admin/weighted_scoring/settings")
        data = json.loads(resp.data)
        assert data["enabled"] is True
        assert data["service_weight"] == 0.5
        assert data["inject_weight"] == 2.0
        assert data["flag_weight"] == 1.5

    def test_non_admin_cannot_update_weighted_scoring(self):
        """Non-admin users should not be able to update settings"""
        self.login("blueuser", "pass")
        resp = self.client.post(
            "/api/admin/weighted_scoring/settings",
            data=json.dumps({"enabled": True}),
            content_type="application/json",
        )
        assert resp.status_code == 403

    def test_weights_in_response_when_enabled(self):
        """Weights should be included in response when weighted scoring enabled"""
        setting = Setting.get_setting("weighted_scoring_enabled")
        setting.value = True
        self.session.commit()
        Setting.clear_cache()

        resp = self.client.get("/api/scoreboard/get_bar_data")
        data = json.loads(resp.data)
        assert "weights" in data
        assert "service" in data["weights"]
        assert "inject" in data["weights"]
        assert "flag" in data["weights"]
