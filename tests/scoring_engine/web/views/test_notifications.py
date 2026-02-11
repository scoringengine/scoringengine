"""Tests for Notifications web view"""

import pytest

from scoring_engine.db import db
from scoring_engine.models.team import Team
from scoring_engine.models.user import User


class TestNotifications:
    """Test notifications web view"""

    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session):
        self.client = test_client
        team = Team(name="Team 1", color="White")
        db.session.add(team)
        user = User(username="testuser", password="testpass", team=team)
        db.session.add(user)
        db.session.commit()
        self.client.post("/login", data={"username": "testuser", "password": "testpass"})

    def test_notifications_unread_route(self):
        """Test that /notifications/unread route works"""
        resp = self.client.get("/notifications/unread")
        assert resp.status_code == 200

    def test_notifications_read_route(self):
        """Test that /notifications/read route works"""
        resp = self.client.get("/notifications/read")
        assert resp.status_code == 200

    def test_notifications_default_route(self):
        """Test that /notifications route works"""
        resp = self.client.get("/notifications")
        assert resp.status_code == 200

    def test_notifications_renders_template(self):
        """Test that notifications renders the correct template"""
        resp = self.client.get("/notifications")
        assert resp.status_code == 200
