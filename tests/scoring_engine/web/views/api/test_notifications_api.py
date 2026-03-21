"""Tests for Notifications API endpoints."""

import datetime

import pytest

from scoring_engine.db import db
from scoring_engine.models.notifications import Notification


class TestNotificationsAPI:
    """Tests for /api/notifications endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self, test_client, three_teams):
        self.client = test_client
        self.teams = three_teams
        self.blue_team = three_teams["blue_team"]
        self.red_team = three_teams["red_team"]

    def login(self, username):
        self.client.post("/login", data={"username": username, "password": "testpass"}, follow_redirects=True)

    def _create_notification(self, team, message="Test notification", target="/services", is_read=False):
        n = Notification(
            message=message,
            target=target,
            team_id=team.id,
            is_read=is_read,
            created=datetime.datetime.now(datetime.UTC),
        )
        db.session.add(n)
        db.session.commit()
        return n

    # --- GET /api/notifications ---

    def test_notifications_requires_auth(self):
        resp = self.client.get("/api/notifications")
        assert resp.status_code == 302

    def test_notifications_returns_all(self):
        self._create_notification(self.blue_team, "Unread msg", is_read=False)
        self._create_notification(self.blue_team, "Read msg", is_read=True)

        self.login("blueuser")
        resp = self.client.get("/api/notifications")
        assert resp.status_code == 200
        data = resp.json
        assert len(data) == 2
        # Should include is_read field
        assert all("is_read" in n for n in data)

    def test_notifications_only_own_team(self):
        self._create_notification(self.blue_team, "Blue notification")
        self._create_notification(self.red_team, "Red notification")

        self.login("blueuser")
        resp = self.client.get("/api/notifications")
        data = resp.json
        assert len(data) == 1
        assert data[0]["message"] == "Blue notification"

    def test_notifications_ordered_desc(self):
        self._create_notification(self.blue_team, "First")
        self._create_notification(self.blue_team, "Second")

        self.login("blueuser")
        resp = self.client.get("/api/notifications")
        data = resp.json
        assert data[0]["message"] == "Second"
        assert data[1]["message"] == "First"

    def test_notification_fields(self):
        self._create_notification(self.blue_team, "Check fields", target="/overview")

        self.login("blueuser")
        resp = self.client.get("/api/notifications")
        data = resp.json
        assert len(data) == 1
        n = data[0]
        assert "id" in n
        assert n["message"] == "Check fields"
        assert n["target"] == "/overview"
        assert "created" in n

    # --- GET /api/notifications/read ---

    def test_notifications_read_requires_auth(self):
        resp = self.client.get("/api/notifications/read")
        assert resp.status_code == 302

    def test_notifications_read_filter(self):
        self._create_notification(self.blue_team, "Unread", is_read=False)
        self._create_notification(self.blue_team, "Read", is_read=True)

        self.login("blueuser")
        resp = self.client.get("/api/notifications/read")
        data = resp.json
        assert len(data) == 1
        assert data[0]["message"] == "Read"

    # --- GET /api/notifications/unread ---

    def test_notifications_unread_requires_auth(self):
        resp = self.client.get("/api/notifications/unread")
        assert resp.status_code == 302

    def test_notifications_unread_filter(self):
        self._create_notification(self.blue_team, "Unread", is_read=False)
        self._create_notification(self.blue_team, "Read", is_read=True)

        self.login("blueuser")
        resp = self.client.get("/api/notifications/unread")
        data = resp.json
        assert len(data) == 1
        assert data[0]["message"] == "Unread"

    def test_notifications_empty_when_none(self):
        self.login("blueuser")
        resp = self.client.get("/api/notifications/unread")
        assert resp.json == []

    # --- POST /api/notifications/<id>/read ---

    def test_mark_read_requires_auth(self):
        resp = self.client.post("/api/notifications/1/read")
        assert resp.status_code == 302

    def test_mark_read_success(self):
        n = self._create_notification(self.blue_team, "To read", is_read=False)

        self.login("blueuser")
        resp = self.client.post(f"/api/notifications/{n.id}/read")
        assert resp.status_code == 200
        assert resp.json["status"] == "Success"
        db.session.refresh(n)
        assert n.is_read is True

    def test_mark_read_nonexistent(self):
        self.login("blueuser")
        resp = self.client.post("/api/notifications/99999/read")
        assert resp.status_code == 403
        assert resp.json["status"] == "Unauthorized"

    def test_mark_read_other_teams_notification(self):
        n = self._create_notification(self.red_team, "Red only")

        self.login("blueuser")
        resp = self.client.post(f"/api/notifications/{n.id}/read")
        assert resp.status_code == 403
        assert resp.json["status"] == "Unauthorized"

    # --- POST /api/notifications/read-all ---

    def test_read_all_requires_auth(self):
        resp = self.client.post("/api/notifications/read-all")
        assert resp.status_code == 302

    def test_read_all_marks_all_unread(self):
        self._create_notification(self.blue_team, "Msg1", is_read=False)
        self._create_notification(self.blue_team, "Msg2", is_read=False)
        self._create_notification(self.blue_team, "Msg3", is_read=True)

        self.login("blueuser")
        resp = self.client.post("/api/notifications/read-all")
        assert resp.status_code == 200
        assert resp.json["status"] == "Success"

        # Verify all are now read
        resp = self.client.get("/api/notifications/unread")
        assert resp.json == []

    def test_read_all_does_not_affect_other_teams(self):
        self._create_notification(self.blue_team, "Blue unread", is_read=False)
        red_n = self._create_notification(self.red_team, "Red unread", is_read=False)

        self.login("blueuser")
        self.client.post("/api/notifications/read-all")

        # Red team's notification should still be unread
        db.session.refresh(red_n)
        assert red_n.is_read is False
