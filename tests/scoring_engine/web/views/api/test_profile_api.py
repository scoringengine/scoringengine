"""Tests for Profile API endpoints."""

import pytest

from scoring_engine.db import db
from scoring_engine.models.user import User


class TestProfileUpdatePassword:
    """Tests for POST /api/profile/update_password."""

    @pytest.fixture(autouse=True)
    def setup(self, test_client, three_teams):
        self.client = test_client
        self.teams = three_teams
        self.blue_user = three_teams["blue_user"]

    def login(self, username):
        self.client.post("/login", data={"username": username, "password": "testpass"}, follow_redirects=True)

    def test_requires_auth(self):
        resp = self.client.post("/api/profile/update_password")
        assert resp.status_code == 302

    def test_successful_password_update(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/profile/update_password",
            data={
                "user_id": str(self.blue_user.id),
                "currentpassword": "testpass",
                "password": "newpass123",
                "confirmedpassword": "newpass123",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        # After password change, verify the new password works
        db.session.refresh(self.blue_user)
        assert self.blue_user.check_password("newpass123")

    def test_wrong_current_password(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/profile/update_password",
            data={
                "user_id": str(self.blue_user.id),
                "currentpassword": "wrongpassword",
                "password": "newpass123",
                "confirmedpassword": "newpass123",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        # Password should not have changed
        db.session.refresh(self.blue_user)
        assert self.blue_user.check_password("testpass")

    def test_passwords_do_not_match(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/profile/update_password",
            data={
                "user_id": str(self.blue_user.id),
                "currentpassword": "testpass",
                "password": "newpass123",
                "confirmedpassword": "different456",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        # Password should not have changed
        db.session.refresh(self.blue_user)
        assert self.blue_user.check_password("testpass")

    def test_password_too_long_for_bcrypt(self):
        self.login("blueuser")
        long_password = "a" * 73  # 73 bytes, exceeds 72 byte limit
        resp = self.client.post(
            "/api/profile/update_password",
            data={
                "user_id": str(self.blue_user.id),
                "currentpassword": "testpass",
                "password": long_password,
                "confirmedpassword": long_password,
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        # Password should not have changed
        db.session.refresh(self.blue_user)
        assert self.blue_user.check_password("testpass")

    def test_password_at_max_length(self):
        self.login("blueuser")
        max_password = "b" * 72  # Exactly 72 bytes, should be accepted
        resp = self.client.post(
            "/api/profile/update_password",
            data={
                "user_id": str(self.blue_user.id),
                "currentpassword": "testpass",
                "password": max_password,
                "confirmedpassword": max_password,
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        db.session.refresh(self.blue_user)
        assert self.blue_user.check_password(max_password)

    def test_user_id_mismatch(self):
        """Cannot update another user's password."""
        self.login("blueuser")
        white_user = self.teams["white_user"]
        resp = self.client.post(
            "/api/profile/update_password",
            data={
                "user_id": str(white_user.id),
                "currentpassword": "testpass",
                "password": "newpass123",
                "confirmedpassword": "newpass123",
            },
        )
        assert resp.status_code == 403
        assert resp.json["status"] == "Unauthorized"

    def test_missing_form_fields(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/profile/update_password",
            data={"user_id": str(self.blue_user.id)},
        )
        assert resp.status_code == 403
        assert resp.json["status"] == "Unauthorized"

    def test_missing_all_fields(self):
        self.login("blueuser")
        resp = self.client.post("/api/profile/update_password", data={})
        assert resp.status_code == 403
        assert resp.json["status"] == "Unauthorized"
