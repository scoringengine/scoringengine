"""Tests for attack logging and correlation API endpoints."""
import json
from datetime import datetime, timedelta, timezone

from scoring_engine.models.check import Check
from scoring_engine.models.flag import Flag, FlagTypeEnum, Platform, Perm, Solve
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from tests.scoring_engine.unit_test import UnitTest


class TestAttacksAPI(UnitTest):

    def setup_method(self):
        super().setup_method()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

        # Create teams
        self.white_team = Team(name="White Team", color="White")
        self.red_team = Team(name="Red Team", color="Red")
        self.blue_team1 = Team(name="Blue Team 1", color="Blue")
        self.blue_team2 = Team(name="Blue Team 2", color="Blue")
        self.session.add_all([self.white_team, self.red_team, self.blue_team1, self.blue_team2])

        # Create users
        self.white_user = User(username="admin", password="testpass", team=self.white_team)
        self.blue_user = User(username="blue1", password="testpass", team=self.blue_team1)
        self.session.add_all([self.white_user, self.blue_user])

        # Create services
        self.service1 = Service(
            name="HTTP",
            team=self.blue_team1,
            check_name="HTTP Check",
            host="10.0.0.1",
            port=80,
        )
        self.service2 = Service(
            name="DNS",
            team=self.blue_team1,
            check_name="DNS Check",
            host="10.0.0.2",
            port=53,
        )
        self.session.add_all([self.service1, self.service2])
        self.session.commit()

    def teardown_method(self):
        self.ctx.pop()
        super().teardown_method()

    def login(self, username, password):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    def create_flag(self, platform=Platform.nix, perm=Perm.user, dummy=False):
        """Helper to create a flag."""
        now = datetime.now(timezone.utc)
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=platform,
            perm=perm,
            data={"path": "/tmp/flag.txt"},
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
            dummy=dummy,
        )
        self.session.add(flag)
        self.session.commit()
        return flag

    def create_solve(self, flag, host, team, captured_at=None):
        """Helper to create a solve."""
        solve = Solve(
            flag=flag,
            host=host,
            team=team,
        )
        self.session.add(solve)
        self.session.commit()
        # Set captured_at after commit if specified
        if captured_at:
            solve.captured_at = captured_at
            self.session.commit()
        return solve

    # Authorization tests
    def test_timeline_requires_auth(self):
        """Test that timeline endpoint requires authentication."""
        resp = self.client.get("/api/attacks/timeline")
        assert resp.status_code == 302

    def test_timeline_requires_white_team(self):
        """Test that timeline endpoint requires white team."""
        self.login("blue1", "testpass")
        resp = self.client.get("/api/attacks/timeline")
        assert resp.status_code == 403

    def test_summary_requires_auth(self):
        """Test that summary endpoint requires authentication."""
        resp = self.client.get("/api/attacks/summary")
        assert resp.status_code == 302

    def test_correlation_requires_auth(self):
        """Test that correlation endpoint requires authentication."""
        resp = self.client.get("/api/attacks/correlation")
        assert resp.status_code == 302

    # Timeline tests
    def test_timeline_empty(self):
        """Test timeline with no captures."""
        self.login("admin", "testpass")
        resp = self.client.get("/api/attacks/timeline")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["count"] == 0
        assert data["data"] == []

    def test_timeline_with_captures(self):
        """Test timeline with captures."""
        flag = self.create_flag()
        now = datetime.now(timezone.utc)
        solve = self.create_solve(flag, "10.0.0.1", self.red_team, captured_at=now)

        self.login("admin", "testpass")
        resp = self.client.get("/api/attacks/timeline")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["count"] == 1
        assert data["data"][0]["host"] == "10.0.0.1"
        assert data["data"][0]["red_team"]["name"] == "Red Team"
        assert data["data"][0]["flag"]["platform"] == "nix"

    def test_timeline_excludes_dummy_flags(self):
        """Test that dummy flags are excluded from timeline."""
        real_flag = self.create_flag(dummy=False)
        dummy_flag = self.create_flag(dummy=True)
        self.create_solve(real_flag, "10.0.0.1", self.red_team)
        self.create_solve(dummy_flag, "10.0.0.2", self.red_team)

        self.login("admin", "testpass")
        resp = self.client.get("/api/attacks/timeline")
        data = json.loads(resp.data)
        assert data["count"] == 1
        assert data["data"][0]["host"] == "10.0.0.1"

    def test_timeline_filter_by_team(self):
        """Test timeline filtering by blue team."""
        flag = self.create_flag()
        self.create_solve(flag, "10.0.0.1", self.red_team)  # blue_team1's host
        self.create_solve(flag, "10.0.0.99", self.red_team)  # unknown host

        self.login("admin", "testpass")
        resp = self.client.get(f"/api/attacks/timeline?team_id={self.blue_team1.id}")
        data = json.loads(resp.data)
        assert data["count"] == 1
        assert data["data"][0]["host"] == "10.0.0.1"

    # Summary tests
    def test_summary_empty(self):
        """Test summary with no captures."""
        self.login("admin", "testpass")
        resp = self.client.get("/api/attacks/summary")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["total_captures"] == 0

    def test_summary_with_captures(self):
        """Test summary with various captures."""
        nix_flag = self.create_flag(platform=Platform.nix, perm=Perm.root)
        win_flag = self.create_flag(platform=Platform.windows, perm=Perm.user)

        self.create_solve(nix_flag, "10.0.0.1", self.red_team)
        self.create_solve(win_flag, "10.0.0.1", self.red_team)

        self.login("admin", "testpass")
        resp = self.client.get("/api/attacks/summary")
        data = json.loads(resp.data)

        assert data["total_captures"] == 2
        assert len(data["by_red_team"]) == 1
        assert data["by_red_team"][0]["team"] == "Red Team"
        assert data["by_red_team"][0]["count"] == 2

    # Correlation tests
    def test_correlation_empty(self):
        """Test correlation with no captures."""
        self.login("admin", "testpass")
        resp = self.client.get("/api/attacks/correlation")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["summary"]["total_captures"] == 0

    def test_correlation_capture_with_failure(self):
        """Test correlation finds failures near captures."""
        flag = self.create_flag()
        now = datetime.now(timezone.utc)

        # Create capture
        solve = self.create_solve(flag, "10.0.0.1", self.red_team, captured_at=now)

        # Create round and failing check shortly after capture
        round_obj = Round(number=1)
        self.session.add(round_obj)
        self.session.commit()

        check = Check(
            round=round_obj,
            service=self.service1,
            result=False,
            reason="Connection refused",
            completed_timestamp=now + timedelta(seconds=60),
            completed=True,
        )
        self.session.add(check)
        self.session.commit()

        self.login("admin", "testpass")
        resp = self.client.get("/api/attacks/correlation?window_seconds=300")
        data = json.loads(resp.data)

        assert data["summary"]["total_captures"] == 1
        assert data["summary"]["captures_with_nearby_failures"] == 1
        assert len(data["correlations"]) == 1
        assert data["correlations"][0]["failure_count"] == 1
        assert data["correlations"][0]["likely_caused_by_attack"] is True

    def test_correlation_no_failures_nearby(self):
        """Test correlation when no failures are near capture."""
        flag = self.create_flag()
        now = datetime.now(timezone.utc)

        # Create capture
        solve = self.create_solve(flag, "10.0.0.1", self.red_team, captured_at=now)

        # Create round and passing check
        round_obj = Round(number=1)
        self.session.add(round_obj)
        self.session.commit()

        check = Check(
            round=round_obj,
            service=self.service1,
            result=True,
            completed_timestamp=now + timedelta(seconds=60),
            completed=True,
        )
        self.session.add(check)
        self.session.commit()

        self.login("admin", "testpass")
        resp = self.client.get("/api/attacks/correlation")
        data = json.loads(resp.data)

        assert data["summary"]["total_captures"] == 1
        assert data["summary"]["captures_with_nearby_failures"] == 0

    # Service history tests
    def test_service_history_not_found(self):
        """Test service history for non-existent service."""
        self.login("admin", "testpass")
        resp = self.client.get("/api/attacks/service/99999/history")
        assert resp.status_code == 404

    def test_service_history(self):
        """Test service history shows captures and failures."""
        flag = self.create_flag()
        now = datetime.now(timezone.utc)

        # Create capture on service host
        solve = self.create_solve(flag, "10.0.0.1", self.red_team, captured_at=now)

        # Create failing check
        round_obj = Round(number=1)
        self.session.add(round_obj)
        self.session.commit()

        check = Check(
            round=round_obj,
            service=self.service1,
            result=False,
            reason="Failed",
            completed_timestamp=now + timedelta(seconds=30),
            completed=True,
        )
        self.session.add(check)
        self.session.commit()

        self.login("admin", "testpass")
        resp = self.client.get(f"/api/attacks/service/{self.service1.id}/history")
        assert resp.status_code == 200
        data = json.loads(resp.data)

        assert data["service"]["name"] == "HTTP"
        assert data["total_captures"] == 1
        assert data["total_failures"] == 1
        assert len(data["timeline"]) == 2

        # Check timeline has both capture and failure
        types = [item["type"] for item in data["timeline"]]
        assert "capture" in types
        assert "failure" in types


class TestSolveCapturedAt(UnitTest):
    """Tests for the Solve.captured_at field."""

    def test_solve_captured_at_default(self):
        """Test that captured_at is set by default on new solves."""
        team = Team(name="Red Team", color="Red")
        self.session.add(team)

        now = datetime.now(timezone.utc)
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            perm=Perm.user,
            data={"path": "/tmp/flag"},
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
        )
        self.session.add(flag)
        self.session.commit()

        solve = Solve(host="10.0.0.1", flag=flag, team=team)
        self.session.add(solve)
        self.session.commit()

        # captured_at should be set automatically
        assert solve.captured_at is not None
        # Should be close to now (within 10 seconds)
        time_diff = abs((solve.captured_at.replace(tzinfo=timezone.utc) - now).total_seconds())
        assert time_diff < 10

    def test_solve_localize_captured_at(self):
        """Test localize_captured_at property."""
        team = Team(name="Red Team", color="Red")
        self.session.add(team)

        now = datetime.now(timezone.utc)
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            perm=Perm.user,
            data={"path": "/tmp/flag"},
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
        )
        self.session.add(flag)
        self.session.commit()

        solve = Solve(host="10.0.0.1", flag=flag, team=team)
        self.session.add(solve)
        self.session.commit()

        # localize_captured_at should return a formatted string
        local_time = solve.localize_captured_at
        assert local_time is not None
        assert isinstance(local_time, str)
        # Should contain date components
        assert "-" in local_time  # Date separator
        assert ":" in local_time  # Time separator
