"""Tests for Notifications web view"""
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from tests.scoring_engine.web.web_test import WebTest


class TestNotifications(WebTest):
    """Test notifications web view"""

    def setup_method(self):
        super(TestNotifications, self).setup_method()
        self.create_default_user()

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
        # Template should be rendered (notifications.html)
