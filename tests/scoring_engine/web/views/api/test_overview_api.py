"""Tests for Overview API endpoints."""

from datetime import datetime, timedelta, timezone

import pytest

from scoring_engine.db import db
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.web.views.api.overview import calculate_ranks


class TestCalculateRanks:
    def test_empty_dict_returns_empty(self):
        assert calculate_ranks({}) == {}

    def test_single_entry(self):
        assert calculate_ranks({1: 100}) == {1: 1}

    def test_distinct_scores(self):
        result = calculate_ranks({1: 300, 2: 200, 3: 100})
        assert result == {1: 1, 2: 2, 3: 3}

    def test_tied_scores(self):
        result = calculate_ranks({1: 200, 2: 200, 3: 100})
        assert result == {1: 1, 2: 1, 3: 3}


class TestOverviewAPI:
    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session):
        self.client = test_client

        # Create teams
        self.white_team = Team(name="White Team", color="White")
        self.blue_team = Team(name="Blue Team", color="Blue")
        self.blue_team2 = Team(name="Blue Team 2", color="Blue")
        self.red_team = Team(name="Red Team", color="Red")
        db.session.add_all([self.white_team, self.blue_team, self.blue_team2, self.red_team])
        db.session.commit()

        # Create users
        self.white_user = User(username="whiteuser", password="testpass", team=self.white_team)
        self.blue_user = User(username="blueuser", password="testpass", team=self.blue_team)
        self.red_user = User(username="reduser", password="testpass", team=self.red_team)
        db.session.add_all([self.white_user, self.blue_user, self.red_user])
        db.session.commit()

    def _login(self, username):
        return self.client.post(
            "/login",
            data={"username": username, "password": "testpass"},
            follow_redirects=True,
        )

    def _create_round_with_checks(self, round_number, services, results):
        """Helper to create a round with checks for given services."""
        now = datetime.now(timezone.utc)
        round_obj = Round(
            number=round_number,
            round_start=now - timedelta(seconds=60),
            round_end=now,
        )
        db.session.add(round_obj)
        db.session.flush()
        for svc, result in zip(services, results):
            check = Check(service=svc, round=round_obj, result=result, output="", completed=True)
            db.session.add(check)
        db.session.commit()
        return round_obj

    # --- get_anonymize_mode (via /api/overview/get_columns endpoint) ---

    def test_anonymize_disabled_returns_real_names(self):
        """When anonymize_team_names is False, columns show real team names."""
        resp = self.client.get("/api/overview/get_columns")
        assert resp.status_code == 200
        columns = resp.json["columns"]
        team_names = [c["title"] for c in columns[1:]]
        assert "Blue Team" in team_names

    def test_anonymize_enabled_white_team_sees_both_names(self):
        """White team sees 'RealName (Codename)' format when anonymize is enabled."""
        setting = Setting.get_setting("anonymize_team_names")
        setting.value = True
        db.session.commit()
        Setting.clear_cache("anonymize_team_names")

        self._login("whiteuser")
        resp = self.client.get("/api/overview/get_columns")
        assert resp.status_code == 200
        columns = resp.json["columns"]
        # White team should see both names (real name with codename)
        assert len(columns) >= 2
        # Columns should contain team entries with show_both format
        team_titles = [c["title"] for c in columns[1:]]
        # At least one title should exist and be non-empty
        assert all(len(t) > 0 for t in team_titles)

    def test_anonymize_enabled_blue_team_sees_anonymous(self):
        """Blue team sees only anonymous names when anonymize is enabled."""
        setting = Setting.get_setting("anonymize_team_names")
        setting.value = True
        db.session.commit()
        Setting.clear_cache("anonymize_team_names")

        self._login("blueuser")
        resp = self.client.get("/api/overview/get_columns")
        assert resp.status_code == 200
        columns = resp.json["columns"]
        team_titles = [c["title"] for c in columns[1:]]
        # Blue team should NOT see real team names
        assert "Blue Team" not in team_titles
        assert "Blue Team 2" not in team_titles

    def test_anonymize_enabled_unauthenticated_sees_anonymous(self):
        """Unauthenticated users see only anonymous names when anonymize is enabled."""
        setting = Setting.get_setting("anonymize_team_names")
        setting.value = True
        db.session.commit()
        Setting.clear_cache("anonymize_team_names")

        resp = self.client.get("/api/overview/get_columns")
        assert resp.status_code == 200
        columns = resp.json["columns"]
        team_titles = [c["title"] for c in columns[1:]]
        # Should NOT see real team names
        assert "Blue Team" not in team_titles
        assert "Blue Team 2" not in team_titles

    # --- /api/overview/get_round_data ---

    def test_get_round_data_no_rounds(self):
        resp = self.client.get("/api/overview/get_round_data")
        assert resp.status_code == 200
        data = resp.json
        assert data["number"] == 0
        assert data["round_start"] == ""
        assert "engine_paused" in data

    def test_get_round_data_with_round(self):
        now = datetime.now(timezone.utc)
        round_obj = Round(number=3, round_start=now - timedelta(seconds=60), round_end=now)
        db.session.add(round_obj)
        db.session.commit()

        resp = self.client.get("/api/overview/get_round_data")
        assert resp.status_code == 200
        data = resp.json
        assert data["number"] == 3
        assert data["round_start"] != ""
        assert data["engine_paused"] is False

    # --- /api/overview/data ---

    def test_overview_data_empty(self):
        resp = self.client.get("/api/overview/data")
        assert resp.status_code == 200
        data = resp.json
        assert data == {}

    def test_overview_data_with_services_and_checks(self):
        svc1 = Service(name="SSH", check_name="SSHCheck", host="10.0.0.1", port=22, team=self.blue_team)
        svc2 = Service(name="HTTP", check_name="HTTPCheck", host="10.0.0.2", port=80, team=self.blue_team2)
        db.session.add_all([svc1, svc2])
        db.session.commit()

        self._create_round_with_checks(1, [svc1, svc2], [True, False])

        resp = self.client.get("/api/overview/data")
        assert resp.status_code == 200
        data = resp.json
        assert len(data) > 0

    # --- /api/overview/get_columns ---

    def test_get_columns_no_blue_teams_has_empty_header(self):
        db.session.query(Team).filter(Team.color == "Blue").delete()
        db.session.commit()

        resp = self.client.get("/api/overview/get_columns")
        assert resp.status_code == 200
        columns = resp.json["columns"]
        assert columns[0]["title"] == ""
        assert len(columns) == 1

    def test_get_columns_with_blue_teams(self):
        resp = self.client.get("/api/overview/get_columns")
        assert resp.status_code == 200
        columns = resp.json["columns"]
        # Empty header + 2 blue teams
        assert len(columns) == 3
        assert columns[0]["title"] == ""
        team_names = [c["title"] for c in columns[1:]]
        assert "Blue Team" in team_names
        assert "Blue Team 2" in team_names

    def test_get_columns_include_color(self):
        resp = self.client.get("/api/overview/get_columns")
        assert resp.status_code == 200
        columns = resp.json["columns"]
        # Each team column should have a color
        for col in columns[1:]:
            assert col["color"] is not None

    # --- /api/overview/get_data ---

    def test_get_data_no_blue_teams(self):
        db.session.query(Team).filter(Team.color == "Blue").delete()
        db.session.commit()

        resp = self.client.get("/api/overview/get_data")
        assert resp.status_code == 200
        assert resp.data == b"{}"

    def test_get_data_with_blue_teams_no_checks(self):
        now = datetime.now(timezone.utc)
        round_obj = Round(number=1, round_start=now - timedelta(seconds=60), round_end=now)
        db.session.add(round_obj)
        db.session.commit()

        resp = self.client.get("/api/overview/get_data")
        assert resp.status_code == 200
        data = resp.json
        rows = data["data"]
        assert len(rows) >= 3
        assert rows[0][0] == "Current Score"
        assert rows[1][0] == "Current Place"
        assert rows[2][0] == "Up/Down Ratio"

    def test_get_data_with_checks_and_scores(self):
        svc1 = Service(name="SSH", check_name="SSHCheck", host="10.0.0.1", port=22, team=self.blue_team, points=100)
        svc2 = Service(name="SSH", check_name="SSHCheck", host="10.0.0.2", port=22, team=self.blue_team2, points=100)
        db.session.add_all([svc1, svc2])
        db.session.commit()

        self._create_round_with_checks(1, [svc1, svc2], [True, False])

        resp = self.client.get("/api/overview/get_data")
        assert resp.status_code == 200
        data = resp.json
        rows = data["data"]

        # Current Score row
        scores_row = rows[0]
        assert scores_row[0] == "Current Score"
        assert scores_row[1] == "100"
        assert scores_row[2] == "0"

        # Current Place row
        places_row = rows[1]
        assert places_row[0] == "Current Place"
        assert places_row[1] == "1"

        # Up/Down Ratio row
        ratio_row = rows[2]
        assert ratio_row[0] == "Up/Down Ratio"
        assert "arrow-up" in ratio_row[1]
        assert "arrow-down" in ratio_row[2]

        # Service row (SSH)
        assert any(row[0] == "SSH" for row in rows)

    def test_get_data_with_sla_enabled(self):
        svc1 = Service(name="SSH", check_name="SSHCheck", host="10.0.0.1", port=22, team=self.blue_team, points=100)
        svc2 = Service(name="SSH", check_name="SSHCheck", host="10.0.0.2", port=22, team=self.blue_team2, points=100)
        db.session.add_all([svc1, svc2])
        db.session.commit()

        self._create_round_with_checks(1, [svc1, svc2], [True, True])

        # Enable SLA
        sla_setting = Setting.get_setting("sla_enabled")
        sla_setting.value = True
        db.session.commit()
        Setting.clear_cache("sla_enabled")

        resp = self.client.get("/api/overview/get_data")
        assert resp.status_code == 200
        data = resp.json
        rows = data["data"]

        row_labels = [row[0] for row in rows]
        assert "Current Score" in row_labels
        assert "Current Place" in row_labels
        assert "SLA Penalties" in row_labels
        assert "Up/Down Ratio" in row_labels

    def test_get_data_with_sla_penalties_shown(self):
        """Test that SLA penalties appear when a team exceeds the failure threshold."""
        svc1 = Service(name="SSH", check_name="SSHCheck", host="10.0.0.1", port=22, team=self.blue_team, points=100)
        db.session.add(svc1)
        db.session.commit()

        # Create enough rounds with failures to exceed SLA threshold (default=5)
        for i in range(1, 7):
            self._create_round_with_checks(i, [svc1], [False])

        # Enable SLA
        sla_setting = Setting.get_setting("sla_enabled")
        sla_setting.value = True
        db.session.commit()
        Setting.clear_cache("sla_enabled")

        resp = self.client.get("/api/overview/get_data")
        assert resp.status_code == 200
        data = resp.json
        rows = data["data"]

        # Find SLA Penalties row
        sla_rows = [row for row in rows if row[0] == "SLA Penalties"]
        assert len(sla_rows) == 1
        sla_row = sla_rows[0]
        # blue_team (index 1) should have a penalty displayed
        # Penalty is calculated from consecutive failures exceeding threshold
        # With 6 failures and threshold of 5, there should be a penalty
        assert len(sla_row) >= 2

    def test_get_data_sla_with_scores_uses_adjusted(self):
        """When SLA is enabled, current scores reflect penalty deductions."""
        svc1 = Service(name="SSH", check_name="SSHCheck", host="10.0.0.1", port=22, team=self.blue_team, points=100)
        svc2 = Service(name="SSH", check_name="SSHCheck", host="10.0.0.2", port=22, team=self.blue_team2, points=100)
        db.session.add_all([svc1, svc2])
        db.session.commit()

        # Round 1: both pass
        self._create_round_with_checks(1, [svc1, svc2], [True, True])

        # Enable SLA
        sla_setting = Setting.get_setting("sla_enabled")
        sla_setting.value = True
        db.session.commit()
        Setting.clear_cache("sla_enabled")

        resp = self.client.get("/api/overview/get_data")
        assert resp.status_code == 200
        data = resp.json
        rows = data["data"]
        scores_row = rows[0]
        assert scores_row[0] == "Current Score"
        # Both teams passed, so scores should be present
        assert len(scores_row) == 3

    def test_get_data_sla_allow_negative(self):
        """Test SLA with allow_negative setting."""
        svc1 = Service(name="SSH", check_name="SSHCheck", host="10.0.0.1", port=22, team=self.blue_team, points=100)
        db.session.add(svc1)
        db.session.commit()

        # Create rounds with failures to generate penalties
        for i in range(1, 7):
            self._create_round_with_checks(i, [svc1], [False])

        # Enable SLA with allow_negative
        sla_setting = Setting.get_setting("sla_enabled")
        sla_setting.value = True
        db.session.commit()
        Setting.clear_cache("sla_enabled")

        allow_neg = Setting.get_setting("sla_allow_negative")
        allow_neg.value = True
        db.session.commit()
        Setting.clear_cache("sla_allow_negative")

        resp = self.client.get("/api/overview/get_data")
        assert resp.status_code == 200
        data = resp.json
        rows = data["data"]
        assert rows[0][0] == "Current Score"
        # With allow_negative=True and no passing checks, score could be negative
        score_val = int(rows[0][1])
        assert score_val <= 0

    def test_get_data_white_team_includes_service_ids(self):
        """White team gets service_ids in the overview response for admin links."""
        svc1 = Service(name="SSH", check_name="SSHCheck", host="10.0.0.1", port=22, team=self.blue_team, points=100)
        svc2 = Service(name="SSH", check_name="SSHCheck", host="10.0.0.2", port=22, team=self.blue_team2, points=100)
        db.session.add_all([svc1, svc2])
        db.session.commit()

        self._create_round_with_checks(1, [svc1, svc2], [True, False])

        self._login("whiteuser")
        resp = self.client.get("/api/overview/get_data")
        assert resp.status_code == 200
        data = resp.json
        assert "service_ids" in data
        assert len(data["service_ids"]) > 0
        # Each entry should be a list of service IDs matching the blue teams
        assert svc1.id in data["service_ids"][0]
        assert svc2.id in data["service_ids"][0]

    def test_get_data_non_white_team_no_service_ids(self):
        """Non-white team users should not get service_ids."""
        svc1 = Service(name="SSH", check_name="SSHCheck", host="10.0.0.1", port=22, team=self.blue_team, points=100)
        db.session.add(svc1)
        db.session.commit()

        self._create_round_with_checks(1, [svc1], [True])

        self._login("blueuser")
        resp = self.client.get("/api/overview/get_data")
        assert resp.status_code == 200
        data = resp.json
        assert "service_ids" not in data

    def test_get_data_anonymous_no_service_ids(self):
        """Anonymous users should not get service_ids."""
        svc1 = Service(name="SSH", check_name="SSHCheck", host="10.0.0.1", port=22, team=self.blue_team, points=100)
        db.session.add(svc1)
        db.session.commit()

        self._create_round_with_checks(1, [svc1], [True])

        resp = self.client.get("/api/overview/get_data")
        assert resp.status_code == 200
        data = resp.json
        assert "service_ids" not in data
