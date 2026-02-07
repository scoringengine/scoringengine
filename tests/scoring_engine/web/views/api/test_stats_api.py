"""Tests for Stats API endpoint"""

from datetime import datetime, timedelta, timezone

import pytest

from scoring_engine.db import db
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.models.user import User


class TestStatsAPI:
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
        self.blue_user2 = User(username="blueuser2", password="testpass", team=self.blue_team2)
        self.red_user = User(username="reduser", password="testpass", team=self.red_team)
        db.session.add_all([self.white_user, self.blue_user, self.blue_user2, self.red_user])
        db.session.commit()

    def login(self, username, password="testpass"):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    def logout(self):
        return self.client.get("/logout", follow_redirects=True)

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

    # --- Auth / Authorization Tests ---

    def test_stats_api_requires_auth(self):
        """Unauthenticated request returns 302 redirect to login"""
        resp = self.client.get("/api/stats")
        assert resp.status_code == 302
        assert "/login?" in resp.location

    def test_stats_api_red_team_unauthorized(self):
        """Red team gets 403"""
        self.login("reduser")
        resp = self.client.get("/api/stats")
        assert resp.status_code == 403
        assert resp.json["status"] == "Unauthorized"

    # --- Response Structure Tests ---

    def test_stats_api_blue_team_response_structure(self):
        """Blue team response has data and summary keys with service_breakdown"""
        svc = Service(name="SSH", check_name="SSH Check", host="10.0.0.1", team=self.blue_team)
        db.session.add(svc)
        db.session.commit()
        self._create_round_with_checks(1, [svc], [True])

        self.login("blueuser")
        resp = self.client.get("/api/stats")
        assert resp.status_code == 200

        data = resp.json
        assert "data" in data
        assert "summary" in data
        assert len(data["data"]) == 1

        round_entry = data["data"][0]
        assert "round_id" in round_entry
        assert "start_time" in round_entry
        assert "end_time" in round_entry
        assert "total_seconds" in round_entry
        assert "num_up_services" in round_entry
        assert "num_down_services" in round_entry
        assert "service_breakdown" in round_entry
        assert "SSH" in round_entry["service_breakdown"]

    # --- Filtering Tests ---

    def test_stats_api_blue_team_sees_own_services(self):
        """Blue team only sees their own team's services"""
        svc1 = Service(name="SSH", check_name="SSH Check", host="10.0.0.1", team=self.blue_team)
        svc2 = Service(name="DNS", check_name="DNS Check", host="10.0.0.2", team=self.blue_team2)
        db.session.add_all([svc1, svc2])
        db.session.commit()
        self._create_round_with_checks(1, [svc1, svc2], [True, False])

        self.login("blueuser")
        resp = self.client.get("/api/stats")
        data = resp.json

        assert "SSH" in data["summary"]
        assert "DNS" not in data["summary"]
        assert data["data"][0]["service_breakdown"].get("DNS") is None

    def test_stats_api_white_team_sees_all(self):
        """White team sees all teams' services"""
        svc1 = Service(name="SSH", check_name="SSH Check", host="10.0.0.1", team=self.blue_team)
        svc2 = Service(name="DNS", check_name="DNS Check", host="10.0.0.2", team=self.blue_team2)
        db.session.add_all([svc1, svc2])
        db.session.commit()
        self._create_round_with_checks(1, [svc1, svc2], [True, False])

        self.login("whiteuser")
        resp = self.client.get("/api/stats")
        data = resp.json

        assert "SSH" in data["summary"]
        assert "DNS" in data["summary"]

    # --- Per-Round Breakdown Tests ---

    def test_stats_api_per_round_breakdown(self):
        """Verify correct up/down counts per service per round"""
        svc_ssh = Service(name="SSH", check_name="SSH Check", host="10.0.0.1", team=self.blue_team)
        svc_dns = Service(name="DNS", check_name="DNS Check", host="10.0.0.2", team=self.blue_team)
        db.session.add_all([svc_ssh, svc_dns])
        db.session.commit()

        self._create_round_with_checks(1, [svc_ssh, svc_dns], [True, False])
        self._create_round_with_checks(2, [svc_ssh, svc_dns], [False, True])

        self.login("blueuser")
        resp = self.client.get("/api/stats")
        data = resp.json

        round2 = data["data"][0]
        round1 = data["data"][1]

        assert round1["round_id"] < round2["round_id"]

        assert round1["service_breakdown"]["SSH"] == {"up": 1, "down": 0}
        assert round1["service_breakdown"]["DNS"] == {"up": 0, "down": 1}

        assert round2["service_breakdown"]["SSH"] == {"up": 0, "down": 1}
        assert round2["service_breakdown"]["DNS"] == {"up": 1, "down": 0}

    # --- Summary Totals Test ---

    def test_stats_api_summary_totals(self):
        """Verify all-time aggregation in summary"""
        svc = Service(name="HTTP", check_name="HTTP Check", host="10.0.0.1", team=self.blue_team)
        db.session.add(svc)
        db.session.commit()

        self._create_round_with_checks(1, [svc], [True])
        self._create_round_with_checks(2, [svc], [False])
        self._create_round_with_checks(3, [svc], [True])

        self.login("blueuser")
        resp = self.client.get("/api/stats")
        data = resp.json

        assert data["summary"]["HTTP"]["up"] == 2
        assert data["summary"]["HTTP"]["down"] == 1
        assert data["summary"]["HTTP"]["total"] == 3

    # --- Empty State Test ---

    def test_stats_api_no_rounds(self):
        """Empty data and summary when no rounds exist"""
        self.login("blueuser")
        resp = self.client.get("/api/stats")
        assert resp.status_code == 200

        data = resp.json
        assert data["data"] == []
        assert data["summary"] == {}
