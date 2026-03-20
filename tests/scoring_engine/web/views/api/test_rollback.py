"""Tests for the score rollback API endpoints."""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from scoring_engine.db import db
from scoring_engine.models.check import Check
from scoring_engine.models.kb import KB
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team
from scoring_engine.models.user import User


class TestScoreRollback:
    @pytest.fixture(autouse=True)
    def mock_sleep(self):
        """Mock time.sleep so rollback's engine-pause wait doesn't slow tests."""
        with patch("scoring_engine.web.views.api.admin.time.sleep"):
            yield

    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session):
        self.client = test_client

        # Create teams
        self.white_team = Team(name="White Team", color="White")
        self.blue_team = Team(name="Blue Team 1", color="Blue")
        db.session.add_all([self.white_team, self.blue_team])
        db.session.commit()

        # Create users
        self.white_user = User(username="whiteuser", password="testpass", team=self.white_team)
        self.blue_user = User(username="blueuser", password="testpass", team=self.blue_team)
        db.session.add_all([self.white_user, self.blue_user])
        db.session.commit()

        # Create a service
        self.service = Service(
            name="TestService",
            check_name="ICMPCheck",
            host="192.168.1.1",
            port=0,
            points=100,
            team=self.blue_team,
        )
        db.session.add(self.service)
        db.session.commit()

    def login_white_team(self):
        return self.client.post(
            "/login",
            data={"username": "whiteuser", "password": "testpass"},
            follow_redirects=True,
        )

    def login_blue_team(self):
        return self.client.post(
            "/login",
            data={"username": "blueuser", "password": "testpass"},
            follow_redirects=True,
        )

    def create_rounds(self, count):
        """Helper to create test rounds with checks."""
        for i in range(1, count + 1):
            round_obj = Round(
                number=i,
                round_start=datetime.now(timezone.utc),
                round_end=datetime.now(timezone.utc),
            )
            db.session.add(round_obj)
            db.session.commit()

            check = Check(round=round_obj, service=self.service, result=True, reason="Test check")
            db.session.add(check)

            kb = KB(round_num=i, name="task_ids", value="{}")
            db.session.add(kb)

        db.session.commit()

    # === Rollback Preview Tests ===

    def test_preview_requires_authentication(self):
        resp = self.client.post("/api/admin/rollback/preview", json={"round_number": 1})
        assert resp.status_code == 302

    def test_preview_requires_white_team(self):
        self.login_blue_team()
        resp = self.client.post("/api/admin/rollback/preview", json={"round_number": 1})
        assert resp.status_code == 403

    def test_preview_requires_round_number(self):
        self.login_white_team()
        resp = self.client.post("/api/admin/rollback/preview", json={})
        assert resp.status_code == 400

    def test_preview_no_rounds(self):
        self.login_white_team()
        resp = self.client.post("/api/admin/rollback/preview", json={"round_number": 1})
        assert resp.status_code == 200
        data = resp.json
        assert data["current_round"] == 0
        assert data["will_delete"]["rounds"] == 0

    def test_preview_shows_correct_counts(self):
        self.create_rounds(5)
        self.login_white_team()
        resp = self.client.post("/api/admin/rollback/preview", json={"round_number": 3})
        assert resp.status_code == 200
        data = resp.json
        assert data["current_round"] == 5
        assert data["round_number"] == 3
        assert data["will_delete"]["rounds"] == 3
        assert data["will_delete"]["checks"] == 3
        assert data["will_delete"]["kb_entries"] == 3

    # === Rollback Tests ===

    def test_rollback_requires_authentication(self):
        resp = self.client.post("/api/admin/rollback", json={"round_number": 1, "confirm": True})
        assert resp.status_code == 302

    def test_rollback_requires_white_team(self):
        self.login_blue_team()
        resp = self.client.post("/api/admin/rollback", json={"round_number": 1, "confirm": True})
        assert resp.status_code == 403

    def test_rollback_requires_round_number(self):
        self.login_white_team()
        resp = self.client.post("/api/admin/rollback", json={"confirm": True})
        assert resp.status_code == 400
        assert "round_number is required" in resp.json["message"]

    def test_rollback_requires_confirm(self):
        self.create_rounds(5)
        self.login_white_team()
        resp = self.client.post("/api/admin/rollback", json={"round_number": 3})
        assert resp.status_code == 400
        assert "confirm" in resp.json["message"]

    def test_rollback_no_rounds(self):
        self.login_white_team()
        resp = self.client.post("/api/admin/rollback", json={"round_number": 1, "confirm": True})
        assert resp.status_code == 400
        assert "No rounds exist" in resp.json["message"]

    def test_rollback_round_exceeds_current(self):
        self.create_rounds(5)
        self.login_white_team()
        resp = self.client.post("/api/admin/rollback", json={"round_number": 10, "confirm": True})
        assert resp.status_code == 400
        assert "exceeds current round" in resp.json["message"]

    def test_rollback_success(self):
        self.create_rounds(5)
        self.login_white_team()

        assert db.session.query(Round).count() == 5
        assert db.session.query(Check).count() == 5
        assert db.session.query(KB).count() == 5

        resp = self.client.post("/api/admin/rollback", json={"round_number": 3, "confirm": True})
        assert resp.status_code == 200
        data = resp.json

        assert data["status"] == "success"
        assert data["deleted"]["rounds"] == 3
        assert data["deleted"]["checks"] == 3
        assert data["deleted"]["kb_entries"] == 3
        assert data["new_current_round"] == 2

        assert db.session.query(Round).count() == 2
        assert db.session.query(Check).count() == 2
        assert db.session.query(KB).count() == 2

        remaining = [r.number for r in db.session.query(Round.number).all()]
        assert remaining == [1, 2]

    def test_rollback_all_rounds(self):
        self.create_rounds(5)
        self.login_white_team()

        resp = self.client.post("/api/admin/rollback", json={"round_number": 1, "confirm": True})
        assert resp.status_code == 200
        data = resp.json

        assert data["deleted"]["rounds"] == 5
        assert data["new_current_round"] == 0
        assert db.session.query(Round).count() == 0
        assert db.session.query(Check).count() == 0
        assert db.session.query(KB).count() == 0

    def test_rollback_invalid_round_number(self):
        self.login_white_team()

        resp = self.client.post("/api/admin/rollback", json={"round_number": "abc", "confirm": True})
        assert resp.status_code == 400

        resp = self.client.post("/api/admin/rollback", json={"round_number": 0, "confirm": True})
        assert resp.status_code == 400

        resp = self.client.post("/api/admin/rollback", json={"round_number": -1, "confirm": True})
        assert resp.status_code == 400

    def test_rollback_unpauses_engine_after_completion(self):
        """Rollback should pause engine during operation and restore original pause state."""
        self.create_rounds(5)
        self.login_white_team()

        # Engine should not be paused before rollback
        Setting.clear_cache("engine_paused")
        assert not Setting.get_setting("engine_paused").value

        resp = self.client.post("/api/admin/rollback", json={"round_number": 3, "confirm": True})
        assert resp.status_code == 200

        # Engine should be unpaused after rollback completes
        Setting.clear_cache("engine_paused")
        assert not Setting.get_setting("engine_paused").value

    def test_rollback_preserves_already_paused_state(self):
        """If engine was already paused, rollback should leave it paused."""
        self.create_rounds(5)
        self.login_white_team()

        # Pause the engine first
        setting = Setting.get_setting("engine_paused")
        setting.value = True
        db.session.add(setting)
        db.session.commit()
        Setting.clear_cache("engine_paused")

        resp = self.client.post("/api/admin/rollback", json={"round_number": 3, "confirm": True})
        assert resp.status_code == 200

        # Engine should still be paused (not unpaused by rollback)
        Setting.clear_cache("engine_paused")
        assert Setting.get_setting("engine_paused").value
