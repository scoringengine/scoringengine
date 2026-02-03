import json
from datetime import datetime, timedelta, timezone

from scoring_engine.models.flag import PersistenceSession, Platform
from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from tests.scoring_engine.unit_test import UnitTest


class TestAPIPersistence(UnitTest):
    """Tests for the persistence tracking API endpoints."""

    def setup_method(self):
        super(TestAPIPersistence, self).setup_method()
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    def create_white_team_user(self):
        """Create a white team user for admin access."""
        team = Team(name="White Team", color="White")
        self.session.add(team)
        user = User(username="whiteuser", password="testpass", team=team)
        self.session.add(user)
        self.session.commit()
        return user

    def create_blue_team_user(self):
        """Create a blue team user."""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)
        user = User(username="blueuser", password="testpass", team=team)
        self.session.add(user)
        self.session.commit()
        return user

    def create_blue_team(self, name="Team 1"):
        """Create a blue team."""
        team = Team(name=name, color="Blue")
        self.session.add(team)
        self.session.commit()
        return team

    def login(self, username, password):
        """Login helper."""
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    def create_persistence_session(self, team, host="webserver.local", platform=Platform.nix, active=True):
        """Create a persistence session for testing."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        session = PersistenceSession(
            host=host,
            team_id=team.id,
            platform=platform,
            started_at=now - timedelta(hours=1),
            last_checkin=now if active else now - timedelta(hours=2),
            ended_at=None if active else now - timedelta(hours=1),
            end_reason=None if active else "timeout",
        )
        self.session.add(session)
        self.session.commit()
        return session

    # =========================================================================
    # Authentication Tests
    # =========================================================================

    def test_persistence_sessions_requires_auth(self):
        """Test that /api/persistence/sessions requires authentication."""
        resp = self.client.get("/api/persistence/sessions")
        assert resp.status_code == 302
        assert "/login" in resp.location

    def test_persistence_sessions_requires_white_team(self):
        """Test that /api/persistence/sessions requires white team."""
        self.create_blue_team_user()
        self.login("blueuser", "testpass")
        resp = self.client.get("/api/persistence/sessions")
        assert resp.status_code == 403

    # =========================================================================
    # Sessions Endpoint Tests
    # =========================================================================

    def test_persistence_sessions_empty(self):
        """Test getting sessions when none exist."""
        self.create_white_team_user()
        self.login("whiteuser", "testpass")
        resp = self.client.get("/api/persistence/sessions")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["count"] == 0
        assert data["data"] == []

    def test_persistence_sessions_with_data(self):
        """Test getting sessions with existing data."""
        self.create_white_team_user()
        blue_team = self.create_blue_team()
        self.create_persistence_session(blue_team)
        self.login("whiteuser", "testpass")

        resp = self.client.get("/api/persistence/sessions")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["count"] == 1
        assert data["data"][0]["host"] == "webserver.local"
        assert data["data"][0]["team_name"] == "Team 1"

    def test_persistence_sessions_filter_active_only(self):
        """Test filtering to active sessions only."""
        self.create_white_team_user()
        blue_team = self.create_blue_team()
        self.create_persistence_session(blue_team, host="active.local", active=True)
        self.create_persistence_session(blue_team, host="ended.local", active=False)
        self.login("whiteuser", "testpass")

        resp = self.client.get("/api/persistence/sessions?active_only=true")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["count"] == 1
        assert data["data"][0]["host"] == "active.local"

    # =========================================================================
    # Summary Endpoint Tests
    # =========================================================================

    def test_persistence_summary(self):
        """Test the persistence summary endpoint."""
        self.create_white_team_user()
        blue_team = self.create_blue_team()
        self.create_persistence_session(blue_team, active=True)
        self.create_persistence_session(blue_team, host="other.local", active=False)
        self.login("whiteuser", "testpass")

        resp = self.client.get("/api/persistence/summary")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["total_sessions"] == 2
        assert data["ended_sessions"] == 1

    # =========================================================================
    # End Session Tests
    # =========================================================================

    def test_persistence_end_session(self):
        """Test manually ending a session."""
        self.create_white_team_user()
        blue_team = self.create_blue_team()
        session = self.create_persistence_session(blue_team)
        self.login("whiteuser", "testpass")

        resp = self.client.post(f"/api/persistence/session/{session.id}/end")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["status"] == "success"
        assert data["session_id"] == session.id

        # Verify session is ended
        self.session.refresh(session)
        assert session.ended_at is not None
        assert session.end_reason == "manual"

    def test_persistence_end_session_not_found(self):
        """Test ending a non-existent session."""
        self.create_white_team_user()
        self.login("whiteuser", "testpass")

        resp = self.client.post("/api/persistence/session/999/end")
        assert resp.status_code == 404

    def test_persistence_end_session_already_ended(self):
        """Test ending an already ended session."""
        self.create_white_team_user()
        blue_team = self.create_blue_team()
        session = self.create_persistence_session(blue_team, active=False)
        self.login("whiteuser", "testpass")

        resp = self.client.post(f"/api/persistence/session/{session.id}/end")
        assert resp.status_code == 400

    # =========================================================================
    # Detect Stale Tests
    # =========================================================================

    def test_persistence_detect_stale(self):
        """Test detecting and ending stale sessions."""
        self.create_white_team_user()
        blue_team = self.create_blue_team()

        # Create a stale session (last_checkin > timeout ago)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        stale_session = PersistenceSession(
            host="stale.local",
            team_id=blue_team.id,
            platform=Platform.nix,
            started_at=now - timedelta(hours=2),
            last_checkin=now - timedelta(minutes=10),  # 10 mins ago, > 5 min default timeout
        )
        self.session.add(stale_session)
        self.session.commit()

        # Add timeout setting (5 minutes = 300 seconds)
        self.session.add(Setting(name="persistence_timeout_seconds", value="300"))
        self.session.commit()
        Setting.clear_cache()

        self.login("whiteuser", "testpass")

        resp = self.client.post("/api/persistence/detect_stale")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["status"] == "success"
        assert data["sessions_ended"] == 1

        # Verify session was ended
        self.session.refresh(stale_session)
        assert stale_session.ended_at is not None
        assert stale_session.end_reason == "timeout"

    # =========================================================================
    # External Beacon API Tests
    # =========================================================================

    def test_beacon_api_disabled_without_psk(self):
        """Test that beacon API returns 503 when PSK not configured."""
        self.create_blue_team("Team 1")

        resp = self.client.post(
            "/api/persistence/beacon",
            json={"team": "Team 1", "host": "test.local", "platform": "nix"},
            headers={"Authorization": "Bearer somepsk"},
        )
        assert resp.status_code == 503

    def test_beacon_api_invalid_psk(self):
        """Test that beacon API rejects invalid PSK."""
        self.create_blue_team("Team 1")
        self.session.add(Setting(name="persistence_beacon_psk", value="correctpsk"))
        self.session.commit()
        Setting.clear_cache()

        resp = self.client.post(
            "/api/persistence/beacon",
            json={"team": "Team 1", "host": "test.local", "platform": "nix"},
            headers={"Authorization": "Bearer wrongpsk"},
        )
        assert resp.status_code == 401

    def test_beacon_api_missing_auth(self):
        """Test that beacon API requires Authorization header."""
        self.create_blue_team("Team 1")
        self.session.add(Setting(name="persistence_beacon_psk", value="testpsk"))
        self.session.commit()
        Setting.clear_cache()

        resp = self.client.post(
            "/api/persistence/beacon",
            json={"team": "Team 1", "host": "test.local", "platform": "nix"},
        )
        assert resp.status_code == 401

    def test_beacon_api_creates_session(self):
        """Test that beacon API creates a new session."""
        blue_team = self.create_blue_team("Team 1")
        self.session.add(Setting(name="persistence_beacon_psk", value="testpsk"))
        self.session.commit()
        Setting.clear_cache()

        resp = self.client.post(
            "/api/persistence/beacon",
            json={"team": "Team 1", "host": "test.local", "platform": "nix"},
            headers={"Authorization": "Bearer testpsk"},
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["status"] == "success"
        assert data["action"] == "created"
        assert data["host"] == "test.local"

        # Verify session was created
        session = self.session.query(PersistenceSession).filter_by(host="test.local").first()
        assert session is not None
        assert session.team_id == blue_team.id
        assert session.platform == Platform.nix

    def test_beacon_api_updates_existing_session(self):
        """Test that beacon API updates existing session."""
        blue_team = self.create_blue_team("Team 1")
        existing_session = self.create_persistence_session(blue_team, host="test.local")
        original_checkin = existing_session.last_checkin

        self.session.add(Setting(name="persistence_beacon_psk", value="testpsk"))
        self.session.commit()
        Setting.clear_cache()

        resp = self.client.post(
            "/api/persistence/beacon",
            json={"team": "Team 1", "host": "test.local", "platform": "win"},
            headers={"Authorization": "Bearer testpsk"},
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["status"] == "success"
        assert data["action"] == "updated"

        # Verify session was updated
        self.session.refresh(existing_session)
        assert existing_session.last_checkin > original_checkin
        assert existing_session.platform == Platform.windows

    def test_beacon_api_with_beacon_id(self):
        """Test that beacon_id creates separate sessions."""
        blue_team = self.create_blue_team("Team 1")
        self.session.add(Setting(name="persistence_beacon_psk", value="testpsk"))
        self.session.commit()
        Setting.clear_cache()

        # Create first beacon
        resp1 = self.client.post(
            "/api/persistence/beacon",
            json={"team": "Team 1", "host": "test.local", "platform": "win", "beacon_id": "beacon1"},
            headers={"Authorization": "Bearer testpsk"},
        )
        assert resp1.status_code == 200

        # Create second beacon on same host
        resp2 = self.client.post(
            "/api/persistence/beacon",
            json={"team": "Team 1", "host": "test.local", "platform": "win", "beacon_id": "beacon2"},
            headers={"Authorization": "Bearer testpsk"},
        )
        assert resp2.status_code == 200

        # Should have two separate sessions
        sessions = self.session.query(PersistenceSession).filter(
            PersistenceSession.team_id == blue_team.id
        ).all()
        assert len(sessions) == 2
        hosts = [s.host for s in sessions]
        assert "test.local:beacon1" in hosts
        assert "test.local:beacon2" in hosts

    def test_beacon_end_api(self):
        """Test that beacon end API ends a session."""
        blue_team = self.create_blue_team("Team 1")
        session = self.create_persistence_session(blue_team, host="test.local")
        self.session.add(Setting(name="persistence_beacon_psk", value="testpsk"))
        self.session.commit()
        Setting.clear_cache()

        resp = self.client.post(
            "/api/persistence/beacon/end",
            json={"team": "Team 1", "host": "test.local", "reason": "exit"},
            headers={"Authorization": "Bearer testpsk"},
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["status"] == "success"

        # Verify session was ended
        self.session.refresh(session)
        assert session.ended_at is not None
        assert session.end_reason == "exit"

    def test_beacon_api_invalid_team(self):
        """Test that beacon API rejects invalid team."""
        self.session.add(Setting(name="persistence_beacon_psk", value="testpsk"))
        self.session.commit()
        Setting.clear_cache()

        resp = self.client.post(
            "/api/persistence/beacon",
            json={"team": "Nonexistent Team", "host": "test.local", "platform": "nix"},
            headers={"Authorization": "Bearer testpsk"},
        )
        assert resp.status_code == 404

    def test_beacon_api_invalid_platform(self):
        """Test that beacon API rejects invalid platform."""
        self.create_blue_team("Team 1")
        self.session.add(Setting(name="persistence_beacon_psk", value="testpsk"))
        self.session.commit()
        Setting.clear_cache()

        resp = self.client.post(
            "/api/persistence/beacon",
            json={"team": "Team 1", "host": "test.local", "platform": "invalid"},
            headers={"Authorization": "Bearer testpsk"},
        )
        assert resp.status_code == 400
