"""Tests for the score rollback API endpoints."""
import json
from datetime import datetime, timezone

from scoring_engine.models.check import Check
from scoring_engine.models.kb import KB
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.web import create_app
from tests.scoring_engine.unit_test import UnitTest


class TestScoreRollback(UnitTest):
    def setup_method(self):
        super(TestScoreRollback, self).setup_method()
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

        # Create teams
        self.white_team = Team(name="White Team", color="White")
        self.blue_team = Team(name="Blue Team 1", color="Blue")
        self.session.add_all([self.white_team, self.blue_team])
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

        # Create a service
        self.service = Service(
            name="TestService",
            check_name="ICMPCheck",
            host="192.168.1.1",
            port=0,
            points=100,
            team=self.blue_team,
        )
        self.session.add(self.service)
        self.session.commit()

    def teardown_method(self):
        self.ctx.pop()
        super(TestScoreRollback, self).teardown_method()

    def login_white_team(self):
        return self.client.post(
            "/login",
            data={"username": "whiteuser", "password": "pass"},
            follow_redirects=True,
        )

    def login_blue_team(self):
        return self.client.post(
            "/login",
            data={"username": "blueuser", "password": "pass"},
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
            self.session.add(round_obj)
            self.session.commit()

            # Create a check for each round
            check = Check(
                round=round_obj,
                service=self.service,
                result=True,
                reason="Test check",
            )
            self.session.add(check)

            # Create KB entry
            kb = KB(
                round_num=i,
                name="task_ids",
                value="{}",
            )
            self.session.add(kb)

        self.session.commit()

    # === Rollback Preview Tests ===

    def test_preview_requires_authentication(self):
        """Test that preview requires login."""
        resp = self.client.post(
            "/api/admin/rollback/preview",
            json={"round_number": 1},
        )
        assert resp.status_code in [302, 401]

    def test_preview_requires_white_team(self):
        """Test that only white team can preview rollback."""
        self.login_blue_team()
        resp = self.client.post(
            "/api/admin/rollback/preview",
            json={"round_number": 1},
        )
        assert resp.status_code == 403

    def test_preview_requires_round_number(self):
        """Test that round_number is required."""
        self.login_white_team()
        resp = self.client.post(
            "/api/admin/rollback/preview",
            json={},
        )
        assert resp.status_code == 400

    def test_preview_no_rounds(self):
        """Test preview when no rounds exist."""
        self.login_white_team()
        resp = self.client.post(
            "/api/admin/rollback/preview",
            json={"round_number": 1},
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["current_round"] == 0
        assert data["will_delete"]["rounds"] == 0

    def test_preview_shows_correct_counts(self):
        """Test that preview shows correct deletion counts."""
        self.create_rounds(5)
        self.login_white_team()

        resp = self.client.post(
            "/api/admin/rollback/preview",
            json={"round_number": 3},
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)

        assert data["current_round"] == 5
        assert data["round_number"] == 3
        # Rounds 3, 4, 5 = 3 rounds
        assert data["will_delete"]["rounds"] == 3
        assert data["will_delete"]["checks"] == 3
        assert data["will_delete"]["kb_entries"] == 3

    # === Rollback Tests ===

    def test_rollback_requires_authentication(self):
        """Test that rollback requires login."""
        resp = self.client.post(
            "/api/admin/rollback",
            json={"round_number": 1, "confirm": True},
        )
        assert resp.status_code in [302, 401]

    def test_rollback_requires_white_team(self):
        """Test that only white team can rollback."""
        self.login_blue_team()
        resp = self.client.post(
            "/api/admin/rollback",
            json={"round_number": 1, "confirm": True},
        )
        assert resp.status_code == 403

    def test_rollback_requires_round_number(self):
        """Test that round_number is required."""
        self.login_white_team()
        resp = self.client.post(
            "/api/admin/rollback",
            json={"confirm": True},
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "round_number is required" in data["message"]

    def test_rollback_requires_confirm(self):
        """Test that confirm=true is required."""
        self.create_rounds(5)
        self.login_white_team()

        resp = self.client.post(
            "/api/admin/rollback",
            json={"round_number": 3},
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "confirm" in data["message"]

    def test_rollback_no_rounds(self):
        """Test rollback when no rounds exist."""
        self.login_white_team()
        resp = self.client.post(
            "/api/admin/rollback",
            json={"round_number": 1, "confirm": True},
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "No rounds exist" in data["message"]

    def test_rollback_round_exceeds_current(self):
        """Test error when round_number exceeds current round."""
        self.create_rounds(5)
        self.login_white_team()

        resp = self.client.post(
            "/api/admin/rollback",
            json={"round_number": 10, "confirm": True},
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "exceeds current round" in data["message"]

    def test_rollback_success(self):
        """Test successful rollback deletes correct data."""
        self.create_rounds(5)
        self.login_white_team()

        # Verify initial state
        assert self.session.query(Round).count() == 5
        assert self.session.query(Check).count() == 5
        assert self.session.query(KB).count() == 5

        resp = self.client.post(
            "/api/admin/rollback",
            json={"round_number": 3, "confirm": True},
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)

        assert data["status"] == "success"
        assert data["deleted"]["rounds"] == 3
        assert data["deleted"]["checks"] == 3
        assert data["deleted"]["kb_entries"] == 3
        assert data["new_current_round"] == 2

        # Verify data was actually deleted
        assert self.session.query(Round).count() == 2
        assert self.session.query(Check).count() == 2
        assert self.session.query(KB).count() == 2

        # Verify correct rounds remain
        remaining_rounds = self.session.query(Round.number).all()
        assert [r.number for r in remaining_rounds] == [1, 2]

    def test_rollback_all_rounds(self):
        """Test rolling back all rounds (from round 1)."""
        self.create_rounds(5)
        self.login_white_team()

        resp = self.client.post(
            "/api/admin/rollback",
            json={"round_number": 1, "confirm": True},
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)

        assert data["deleted"]["rounds"] == 5
        assert data["new_current_round"] == 0

        # All data should be deleted
        assert self.session.query(Round).count() == 0
        assert self.session.query(Check).count() == 0
        assert self.session.query(KB).count() == 0

    def test_rollback_invalid_round_number(self):
        """Test error for invalid round_number values."""
        self.login_white_team()

        # Non-integer
        resp = self.client.post(
            "/api/admin/rollback",
            json={"round_number": "abc", "confirm": True},
        )
        assert resp.status_code == 400

        # Zero
        resp = self.client.post(
            "/api/admin/rollback",
            json={"round_number": 0, "confirm": True},
        )
        assert resp.status_code == 400

        # Negative
        resp = self.client.post(
            "/api/admin/rollback",
            json={"round_number": -1, "confirm": True},
        )
        assert resp.status_code == 400
