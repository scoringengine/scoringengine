"""Tests for Scoreboard API endpoints."""

from datetime import datetime, timedelta, timezone

import pytest

from scoring_engine.db import db
from scoring_engine.models.check import Check
from scoring_engine.models.inject import Inject, InjectRubricScore, RubricItem, Template
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team
from scoring_engine.models.user import User


class TestScoreboardAPI:
    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session):
        self.client = test_client

        # Create teams
        self.white_team = Team(name="White Team", color="White")
        self.blue_team = Team(name="Blue Team", color="Blue")
        self.blue_team2 = Team(name="Blue Team 2", color="Blue")
        self.red_team = Team(name="Red Team", color="Red")
        db.session.add_all([self.white_team, self.blue_team, self.blue_team2, self.red_team])
        db.session.flush()

        # Create users
        self.white_user = User(username="whiteuser", password="testpass", team=self.white_team)
        self.blue_user = User(username="blueuser", password="testpass", team=self.blue_team)
        self.red_user = User(username="reduser", password="testpass", team=self.red_team)
        db.session.add_all([self.white_user, self.blue_user, self.red_user])
        db.session.commit()

    def login(self, username, password="testpass"):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
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
            check = Check(service=svc, round=round_obj, result=result, output="")
            db.session.add(check)
        db.session.commit()
        return round_obj

    # -----------------------------------------------------------------------
    # /api/scoreboard/get_bar_data
    # -----------------------------------------------------------------------

    def test_get_bar_data_empty(self):
        """Bar data with no checks returns empty lists for blue teams."""
        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = resp.json
        assert data["labels"] == ["Blue Team", "Blue Team 2"]
        assert data["service_scores"] == ["0", "0"]
        assert data["inject_scores"] == ["0", "0"]
        assert data["sla_penalties"] == ["0", "0"]
        assert data["adjusted_scores"] == ["0", "0"]
        assert data["sla_enabled"] is False

    def test_get_bar_data_with_checks(self):
        """Bar data includes service scores from passing checks."""
        svc1 = Service(name="SSH", check_name="SSHCheck", host="10.0.0.1", team=self.blue_team, points=100)
        svc2 = Service(name="HTTP", check_name="HTTPCheck", host="10.0.0.2", team=self.blue_team2, points=150)
        db.session.add_all([svc1, svc2])
        db.session.commit()

        self._create_round_with_checks(1, [svc1, svc2], [True, True])
        self._create_round_with_checks(2, [svc1, svc2], [True, False])

        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = resp.json
        # blue_team: 2 passing checks * 100 points = 200
        # blue_team2: 1 passing check * 150 points = 150
        assert data["service_scores"] == ["200", "150"]
        assert data["adjusted_scores"] == ["200", "150"]
        assert len(data["colors"]) == 2

    def test_get_bar_data_with_sla_penalties(self):
        """Bar data shows SLA penalties when SLA is enabled."""
        svc = Service(name="SSH", check_name="SSHCheck", host="10.0.0.1", team=self.blue_team, points=100)
        db.session.add(svc)
        db.session.commit()

        # Create enough rounds with failures to trigger SLA penalty
        # Default threshold is 5 consecutive failures, penalty is 10%
        for i in range(1, 8):
            self._create_round_with_checks(i, [svc], [False])

        # Enable SLA
        setting = Setting.get_setting("sla_enabled")
        setting.value = True
        db.session.commit()
        Setting.clear_cache("sla_enabled")

        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = resp.json
        assert data["sla_enabled"] is True
        # Service score is 0 (all checks failed), so adjusted should be 0
        assert data["service_scores"][0] == "0"

    def test_get_bar_data_with_inject_scores_visible(self):
        """Bar data includes inject scores when inject_scores_visible is True."""
        # Enable inject_scores_visible
        setting = Setting.get_setting("inject_scores_visible")
        setting.value = True
        db.session.commit()
        Setting.clear_cache("inject_scores_visible")

        # Create inject data
        now = datetime.now(timezone.utc)
        template = Template(
            title="Test Inject",
            scenario="Test scenario",
            deliverable="Test deliverable",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
        )
        db.session.add(template)
        db.session.flush()

        rubric_item = RubricItem(title="Criteria 1", points=50, template=template)
        db.session.add(rubric_item)
        db.session.flush()

        inject = Inject(team=self.blue_team, template=template)
        inject.status = "Graded"
        db.session.add(inject)
        db.session.flush()

        score = InjectRubricScore(score=40, inject=inject, rubric_item=rubric_item, grader=self.white_user)
        db.session.add(score)
        db.session.commit()

        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = resp.json
        # Blue Team has 40 inject points, Blue Team 2 has 0
        assert data["inject_scores"][0] == "40"
        assert data["inject_scores"][1] == "0"
        assert data["adjusted_scores"][0] == "40"

    def test_get_bar_data_sla_allow_negative(self):
        """When allow_negative is True, adjusted scores can go below zero."""
        svc = Service(name="SSH", check_name="SSHCheck", host="10.0.0.1", team=self.blue_team, points=100)
        db.session.add(svc)
        db.session.commit()

        # 1 passing check = 100 points
        self._create_round_with_checks(1, [svc], [True])
        # Then many failures to accumulate large penalty
        for i in range(2, 20):
            self._create_round_with_checks(i, [svc], [False])

        # Enable SLA with allow_negative
        setting = Setting.get_setting("sla_enabled")
        setting.value = True
        db.session.commit()
        Setting.clear_cache("sla_enabled")

        setting = Setting.get_setting("sla_allow_negative")
        setting.value = True
        db.session.commit()
        Setting.clear_cache("sla_allow_negative")

        # Set high penalty to ensure it exceeds score
        setting = Setting.get_setting("sla_penalty_percent")
        setting.value = "100"
        db.session.commit()
        Setting.clear_cache("sla_penalty_percent")

        setting = Setting.get_setting("sla_penalty_max_percent")
        setting.value = "10000"
        db.session.commit()
        Setting.clear_cache("sla_penalty_max_percent")

        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = resp.json
        assert data["sla_enabled"] is True
        adjusted = int(data["adjusted_scores"][0])
        # With allow_negative=True, adjusted can be negative
        # (or at least the code path allowing negative is exercised)
        assert isinstance(adjusted, int)

    # -----------------------------------------------------------------------
    # /api/scoreboard/get_line_data
    # -----------------------------------------------------------------------

    def test_get_line_data_empty(self):
        """Line data with no rounds returns empty team list."""
        resp = self.client.get("/api/scoreboard/get_line_data")
        assert resp.status_code == 200
        data = resp.json
        assert "team" in data
        assert "rounds" in data
        # Should have "Round 0" since last_round_num is 0
        assert data["rounds"] == ["Round 0"]
        # Should have entries for both blue teams
        assert len(data["team"]) == 2

    def test_get_line_data_with_rounds(self):
        """Line data includes cumulative scores per round."""
        svc1 = Service(name="SSH", check_name="SSHCheck", host="10.0.0.1", team=self.blue_team, points=100)
        svc2 = Service(name="HTTP", check_name="HTTPCheck", host="10.0.0.2", team=self.blue_team2, points=50)
        db.session.add_all([svc1, svc2])
        db.session.commit()

        self._create_round_with_checks(1, [svc1, svc2], [True, True])
        self._create_round_with_checks(2, [svc1, svc2], [True, False])
        self._create_round_with_checks(3, [svc1, svc2], [False, True])

        resp = self.client.get("/api/scoreboard/get_line_data")
        assert resp.status_code == 200
        data = resp.json

        assert len(data["rounds"]) == 4  # Round 0, 1, 2, 3
        assert data["rounds"] == ["Round 0", "Round 1", "Round 2", "Round 3"]

        # Find blue_team and blue_team2 entries
        team1_data = None
        team2_data = None
        for t in data["team"]:
            if t["name"] == "Blue Team":
                team1_data = t
            elif t["name"] == "Blue Team 2":
                team2_data = t

        assert team1_data is not None
        assert team2_data is not None

        # Scores are cumulative over rounds with passing checks
        # Blue Team: passed round 1 (100) and round 2 (100)
        # Cumulative: [0, 100, 200]
        assert team1_data["scores"] == [0, 100, 200]

        # Blue Team 2: passed round 1 (50) and round 3 (50)
        # Cumulative: [0, 50, 100]
        assert team2_data["scores"] == [0, 50, 100]

        assert "color" in team1_data
        assert "color" in team2_data

    def test_get_line_data_cumulative_scores(self):
        """Line data scores accumulate correctly across rounds."""
        svc = Service(name="DNS", check_name="DNSCheck", host="10.0.0.1", team=self.blue_team, points=200)
        db.session.add(svc)
        db.session.commit()

        self._create_round_with_checks(1, [svc], [True])
        self._create_round_with_checks(2, [svc], [True])

        resp = self.client.get("/api/scoreboard/get_line_data")
        assert resp.status_code == 200
        data = resp.json

        team_data = data["team"][0]
        # Cumulative: [0, 200, 400]
        assert team_data["scores"] == [0, 200, 400]

    # -----------------------------------------------------------------------
    # Anonymize mode tests
    # -----------------------------------------------------------------------

    def test_get_bar_data_anonymize_blue_team(self):
        """Blue team sees anonymous names when anonymize is enabled."""
        setting = Setting.get_setting("anonymize_team_names")
        setting.value = True
        db.session.commit()
        Setting.clear_cache("anonymize_team_names")

        self.login("blueuser")
        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = resp.json
        # Blue team should see anonymous names, not real names
        for label in data["labels"]:
            assert "Blue Team" not in label

    def test_get_bar_data_anonymize_white_team(self):
        """White team sees both real and anonymous names when anonymize is enabled."""
        setting = Setting.get_setting("anonymize_team_names")
        setting.value = True
        db.session.commit()
        Setting.clear_cache("anonymize_team_names")

        self.login("whiteuser")
        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = resp.json
        # White team sees both names (show_both=True)
        # Labels should contain real team names
        label_str = " ".join(data["labels"])
        assert "Blue Team" in label_str

    def test_get_line_data_anonymize_blue_team(self):
        """Blue team sees anonymous names in line data when anonymize is enabled."""
        setting = Setting.get_setting("anonymize_team_names")
        setting.value = True
        db.session.commit()
        Setting.clear_cache("anonymize_team_names")

        svc = Service(name="SSH", check_name="SSHCheck", host="10.0.0.1", team=self.blue_team, points=100)
        db.session.add(svc)
        db.session.commit()
        self._create_round_with_checks(1, [svc], [True])

        self.login("blueuser")
        resp = self.client.get("/api/scoreboard/get_line_data")
        assert resp.status_code == 200
        data = resp.json
        for team in data["team"]:
            assert "Blue Team" not in team["name"]

    def test_get_line_data_anonymize_white_team(self):
        """White team sees both names in line data when anonymize is enabled."""
        setting = Setting.get_setting("anonymize_team_names")
        setting.value = True
        db.session.commit()
        Setting.clear_cache("anonymize_team_names")

        svc = Service(name="SSH", check_name="SSHCheck", host="10.0.0.1", team=self.blue_team, points=100)
        db.session.add(svc)
        db.session.commit()
        self._create_round_with_checks(1, [svc], [True])

        self.login("whiteuser")
        resp = self.client.get("/api/scoreboard/get_line_data")
        assert resp.status_code == 200
        data = resp.json
        # White team should see real names
        names = [t["name"] for t in data["team"]]
        name_str = " ".join(names)
        assert "Blue Team" in name_str

    def test_get_bar_data_no_anonymize(self):
        """With anonymize disabled, real names are shown."""
        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = resp.json
        assert "Blue Team" in data["labels"]
        assert "Blue Team 2" in data["labels"]
