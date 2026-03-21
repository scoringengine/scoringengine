"""Tests for SLA API endpoints."""

from unittest.mock import patch

import pytest

from scoring_engine.db import db
from scoring_engine.models.round import Round
from scoring_engine.models.setting import Setting


class TestSlaPublicAPI:
    @pytest.fixture(autouse=True)
    def setup(self, test_client, three_teams):
        self.client = test_client
        self.white_team = three_teams["white_team"]
        self.blue_team = three_teams["blue_team"]
        self.red_team = three_teams["red_team"]
        self.white_user = three_teams["white_user"]
        self.blue_user = three_teams["blue_user"]
        self.red_user = three_teams["red_user"]

    def login(self, username, password="testpass"):
        return self.client.post("/login", data={"username": username, "password": password}, follow_redirects=True)

    def test_sla_summary_requires_auth(self):
        resp = self.client.get("/api/sla/summary")
        assert resp.status_code == 302

    def test_sla_summary_returns_data(self):
        self.login(self.blue_user.username)
        resp = self.client.get("/api/sla/summary")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "sla_enabled" in data
        assert "penalty_threshold" in data
        assert "penalty_mode" in data
        assert "teams" in data

    def test_sla_team_detail_requires_auth(self):
        resp = self.client.get(f"/api/sla/team/{self.blue_team.id}")
        assert resp.status_code == 302

    def test_sla_team_detail_not_found(self):
        self.login(self.white_user.username)
        resp = self.client.get("/api/sla/team/99999")
        assert resp.status_code == 404

    def test_sla_team_detail_unauthorized_other_team(self):
        self.login(self.blue_user.username)
        resp = self.client.get(f"/api/sla/team/{self.red_team.id}")
        assert resp.status_code == 403

    def test_sla_team_detail_own_team(self):
        self.login(self.blue_user.username)
        resp = self.client.get(f"/api/sla/team/{self.blue_team.id}")
        assert resp.status_code == 200

    def test_sla_team_detail_white_team(self):
        self.login(self.white_user.username)
        resp = self.client.get(f"/api/sla/team/{self.blue_team.id}")
        assert resp.status_code == 200

    def test_sla_config_requires_auth(self):
        resp = self.client.get("/api/sla/config")
        assert resp.status_code == 302

    def test_sla_config_requires_white_team(self):
        self.login(self.blue_user.username)
        resp = self.client.get("/api/sla/config")
        assert resp.status_code == 403

    def test_sla_config_white_team_success(self):
        self.login(self.white_user.username)
        resp = self.client.get("/api/sla/config")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "sla_enabled" in data
        assert "penalty_threshold" in data
        assert "penalty_percent" in data
        assert "penalty_max_percent" in data
        assert "penalty_mode" in data
        assert "allow_negative" in data

    def test_dynamic_scoring_info_requires_auth(self):
        resp = self.client.get("/api/sla/dynamic-scoring")
        assert resp.status_code == 302

    def test_dynamic_scoring_info_returns_data(self):
        self.login(self.blue_user.username)
        resp = self.client.get("/api/sla/dynamic-scoring")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "current_round" in data
        assert "current_multiplier" in data
        assert "current_phase" in data

    def test_dynamic_scoring_early_phase(self):
        self.login(self.blue_user.username)
        # No rounds = round 0, which is <= early_rounds, so "early"
        resp = self.client.get("/api/sla/dynamic-scoring")
        data = resp.get_json()
        assert data["current_phase"] == "early"

    def test_dynamic_scoring_normal_phase(self):
        # Default early_rounds=10, late_start_round=50
        # Create 15 rounds to be past early but before late
        for i in range(1, 16):
            r = Round(number=i)
            db.session.add(r)
        db.session.commit()
        # Set early_rounds low so we're clearly in normal phase
        setting = Setting.get_setting("dynamic_scoring_early_rounds")
        setting.value = "3"
        db.session.commit()
        Setting.clear_cache("dynamic_scoring_early_rounds")
        self.login(self.blue_user.username)
        resp = self.client.get("/api/sla/dynamic-scoring")
        data = resp.get_json()
        assert data["current_phase"] == "normal"

    def test_dynamic_scoring_late_phase(self):
        # Create enough rounds to be in late phase
        for i in range(1, 55):
            r = Round(number=i)
            db.session.add(r)
        db.session.commit()
        self.login(self.blue_user.username)
        resp = self.client.get("/api/sla/dynamic-scoring")
        data = resp.get_json()
        assert data["current_phase"] == "late"


class TestSlaAdminAPI:
    @pytest.fixture(autouse=True)
    def setup(self, test_client, three_teams):
        self.client = test_client
        self.white_user = three_teams["white_user"]
        self.blue_user = three_teams["blue_user"]

    def login(self, username, password="testpass"):
        return self.client.post("/login", data={"username": username, "password": password}, follow_redirects=True)

    # --- SLA Enabled ---

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_toggle_sla_enabled_requires_white(self, mock_cache):
        self.login(self.blue_user.username)
        resp = self.client.post("/api/admin/update_sla_enabled")
        assert resp.status_code == 403

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_toggle_sla_enabled_success(self, mock_cache):
        self.login(self.white_user.username)
        setting = Setting.get_setting("sla_enabled")
        original = setting.value
        resp = self.client.post("/api/admin/update_sla_enabled", follow_redirects=False)
        assert resp.status_code == 302
        Setting.clear_cache("sla_enabled")
        setting = Setting.get_setting("sla_enabled")
        assert setting.value != original

    # --- Penalty Threshold ---

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_penalty_threshold_requires_white(self, mock_cache):
        self.login(self.blue_user.username)
        resp = self.client.post("/api/admin/update_sla_penalty_threshold", data={"sla_penalty_threshold": "5"})
        assert resp.status_code == 403

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_penalty_threshold_success(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post(
            "/api/admin/update_sla_penalty_threshold",
            data={"sla_penalty_threshold": "5"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        Setting.clear_cache("sla_penalty_threshold")
        assert Setting.get_setting("sla_penalty_threshold").value == "5"

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_penalty_threshold_non_integer(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post(
            "/api/admin/update_sla_penalty_threshold",
            data={"sla_penalty_threshold": "abc"},
            follow_redirects=False,
        )
        assert resp.status_code == 302

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_penalty_threshold_zero(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post(
            "/api/admin/update_sla_penalty_threshold",
            data={"sla_penalty_threshold": "0"},
            follow_redirects=False,
        )
        assert resp.status_code == 302

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_penalty_threshold_missing_field(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post("/api/admin/update_sla_penalty_threshold", follow_redirects=False)
        assert resp.status_code == 302

    # --- Penalty Percent ---

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_penalty_percent_success(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post(
            "/api/admin/update_sla_penalty_percent",
            data={"sla_penalty_percent": "10"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        Setting.clear_cache("sla_penalty_percent")
        assert Setting.get_setting("sla_penalty_percent").value == "10"

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_penalty_percent_invalid(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post(
            "/api/admin/update_sla_penalty_percent",
            data={"sla_penalty_percent": "abc"},
            follow_redirects=False,
        )
        assert resp.status_code == 302

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_penalty_percent_missing(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post("/api/admin/update_sla_penalty_percent", follow_redirects=False)
        assert resp.status_code == 302

    # --- Penalty Max Percent ---

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_penalty_max_percent_success(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post(
            "/api/admin/update_sla_penalty_max_percent",
            data={"sla_penalty_max_percent": "50"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        Setting.clear_cache("sla_penalty_max_percent")
        assert Setting.get_setting("sla_penalty_max_percent").value == "50"

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_penalty_max_percent_invalid(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post(
            "/api/admin/update_sla_penalty_max_percent",
            data={"sla_penalty_max_percent": "nope"},
            follow_redirects=False,
        )
        assert resp.status_code == 302

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_penalty_max_percent_missing(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post("/api/admin/update_sla_penalty_max_percent", follow_redirects=False)
        assert resp.status_code == 302

    # --- Penalty Mode ---

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_penalty_mode_success(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post(
            "/api/admin/update_sla_penalty_mode",
            data={"sla_penalty_mode": "exponential"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        Setting.clear_cache("sla_penalty_mode")
        assert Setting.get_setting("sla_penalty_mode").value == "exponential"

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_penalty_mode_all_valid_modes(self, mock_cache):
        self.login(self.white_user.username)
        for mode in ["additive", "flat", "exponential", "next_check_reduction"]:
            resp = self.client.post(
                "/api/admin/update_sla_penalty_mode",
                data={"sla_penalty_mode": mode},
                follow_redirects=False,
            )
            assert resp.status_code == 302

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_penalty_mode_invalid(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post(
            "/api/admin/update_sla_penalty_mode",
            data={"sla_penalty_mode": "invalid_mode"},
            follow_redirects=False,
        )
        assert resp.status_code == 302

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_penalty_mode_missing(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post("/api/admin/update_sla_penalty_mode", follow_redirects=False)
        assert resp.status_code == 302

    # --- Allow Negative ---

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_toggle_allow_negative_requires_white(self, mock_cache):
        self.login(self.blue_user.username)
        resp = self.client.post("/api/admin/update_sla_allow_negative")
        assert resp.status_code == 403

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_toggle_allow_negative_success(self, mock_cache):
        self.login(self.white_user.username)
        setting = Setting.get_setting("sla_allow_negative")
        original = setting.value
        resp = self.client.post("/api/admin/update_sla_allow_negative", follow_redirects=False)
        assert resp.status_code == 302
        Setting.clear_cache("sla_allow_negative")
        setting = Setting.get_setting("sla_allow_negative")
        assert setting.value != original

    # --- Dynamic Scoring Enabled ---

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_toggle_dynamic_scoring_requires_white(self, mock_cache):
        self.login(self.blue_user.username)
        resp = self.client.post("/api/admin/update_dynamic_scoring_enabled")
        assert resp.status_code == 403

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_toggle_dynamic_scoring_success(self, mock_cache):
        self.login(self.white_user.username)
        setting = Setting.get_setting("dynamic_scoring_enabled")
        original = setting.value
        resp = self.client.post("/api/admin/update_dynamic_scoring_enabled", follow_redirects=False)
        assert resp.status_code == 302
        Setting.clear_cache("dynamic_scoring_enabled")
        setting = Setting.get_setting("dynamic_scoring_enabled")
        assert setting.value != original

    # --- Dynamic Scoring Early Rounds ---

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_early_rounds_success(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post(
            "/api/admin/update_dynamic_scoring_early_rounds",
            data={"dynamic_scoring_early_rounds": "3"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        Setting.clear_cache("dynamic_scoring_early_rounds")
        assert Setting.get_setting("dynamic_scoring_early_rounds").value == "3"

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_early_rounds_invalid(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post(
            "/api/admin/update_dynamic_scoring_early_rounds",
            data={"dynamic_scoring_early_rounds": "abc"},
            follow_redirects=False,
        )
        assert resp.status_code == 302

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_early_rounds_missing(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post("/api/admin/update_dynamic_scoring_early_rounds", follow_redirects=False)
        assert resp.status_code == 302

    # --- Dynamic Scoring Early Multiplier ---

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_early_multiplier_success(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post(
            "/api/admin/update_dynamic_scoring_early_multiplier",
            data={"dynamic_scoring_early_multiplier": "1.5"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        Setting.clear_cache("dynamic_scoring_early_multiplier")
        assert Setting.get_setting("dynamic_scoring_early_multiplier").value == "1.5"

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_early_multiplier_invalid(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post(
            "/api/admin/update_dynamic_scoring_early_multiplier",
            data={"dynamic_scoring_early_multiplier": "abc"},
            follow_redirects=False,
        )
        assert resp.status_code == 302

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_early_multiplier_zero(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post(
            "/api/admin/update_dynamic_scoring_early_multiplier",
            data={"dynamic_scoring_early_multiplier": "0"},
            follow_redirects=False,
        )
        assert resp.status_code == 302

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_early_multiplier_negative(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post(
            "/api/admin/update_dynamic_scoring_early_multiplier",
            data={"dynamic_scoring_early_multiplier": "-1"},
            follow_redirects=False,
        )
        assert resp.status_code == 302

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_early_multiplier_missing(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post("/api/admin/update_dynamic_scoring_early_multiplier", follow_redirects=False)
        assert resp.status_code == 302

    # --- Dynamic Scoring Late Start Round ---

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_late_start_round_success(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post(
            "/api/admin/update_dynamic_scoring_late_start_round",
            data={"dynamic_scoring_late_start_round": "15"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        Setting.clear_cache("dynamic_scoring_late_start_round")
        assert Setting.get_setting("dynamic_scoring_late_start_round").value == "15"

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_late_start_round_invalid(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post(
            "/api/admin/update_dynamic_scoring_late_start_round",
            data={"dynamic_scoring_late_start_round": "abc"},
            follow_redirects=False,
        )
        assert resp.status_code == 302

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_late_start_round_missing(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post("/api/admin/update_dynamic_scoring_late_start_round", follow_redirects=False)
        assert resp.status_code == 302

    # --- Dynamic Scoring Late Multiplier ---

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_late_multiplier_success(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post(
            "/api/admin/update_dynamic_scoring_late_multiplier",
            data={"dynamic_scoring_late_multiplier": "2.0"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        Setting.clear_cache("dynamic_scoring_late_multiplier")
        assert Setting.get_setting("dynamic_scoring_late_multiplier").value == "2.0"

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_late_multiplier_invalid(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post(
            "/api/admin/update_dynamic_scoring_late_multiplier",
            data={"dynamic_scoring_late_multiplier": "abc"},
            follow_redirects=False,
        )
        assert resp.status_code == 302

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_late_multiplier_negative(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post(
            "/api/admin/update_dynamic_scoring_late_multiplier",
            data={"dynamic_scoring_late_multiplier": "-0.5"},
            follow_redirects=False,
        )
        assert resp.status_code == 302

    @patch("scoring_engine.web.views.api.sla._clear_scoring_cache")
    def test_update_late_multiplier_missing(self, mock_cache):
        self.login(self.white_user.username)
        resp = self.client.post("/api/admin/update_dynamic_scoring_late_multiplier", follow_redirects=False)
        assert resp.status_code == 302
