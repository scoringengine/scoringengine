import pytest

from scoring_engine.db import db
from scoring_engine.models.account import Account
from scoring_engine.models.service import Service
from scoring_engine.web.views.api.service import MAX_HOST_LENGTH, MAX_PASSWORD_LENGTH, MAX_USERNAME_LENGTH


class TestUpdateAccountLengthValidation:
    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session, blue_login):
        self.client, self.teams = blue_login
        self.service = Service(
            name="TestSSH",
            check_name="SSHCheck",
            host="10.0.0.1",
            port=22,
            team=self.teams["blue_team"],
        )
        db.session.add(self.service)
        db.session.flush()
        self.account = Account(username="admin", password="secret", service=self.service)
        db.session.add(self.account)
        db.session.commit()

    def test_username_at_max_length(self):
        value = "a" * MAX_USERNAME_LENGTH
        resp = self.client.post(
            "/api/service/update_account",
            data={"pk": self.account.id, "name": "username", "value": value},
        )
        assert resp.json.get("status") == "Updated Account Information"

    def test_username_exceeds_max_length(self):
        value = "a" * (MAX_USERNAME_LENGTH + 1)
        resp = self.client.post(
            "/api/service/update_account",
            data={"pk": self.account.id, "name": "username", "value": value},
        )
        assert "error" in resp.json
        assert str(MAX_USERNAME_LENGTH) in resp.json["error"]

    def test_password_at_max_length(self):
        value = "a" * MAX_PASSWORD_LENGTH
        resp = self.client.post(
            "/api/service/update_account",
            data={"pk": self.account.id, "name": "password", "value": value},
        )
        assert resp.json.get("status") == "Updated Account Information"

    def test_password_exceeds_max_length(self):
        value = "a" * (MAX_PASSWORD_LENGTH + 1)
        resp = self.client.post(
            "/api/service/update_account",
            data={"pk": self.account.id, "name": "password", "value": value},
        )
        assert "error" in resp.json
        assert str(MAX_PASSWORD_LENGTH) in resp.json["error"]


class TestUpdateHostLengthValidation:
    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session, blue_login):
        self.client, self.teams = blue_login
        self.service = Service(
            name="TestSSH",
            check_name="SSHCheck",
            host="10.0.0.1",
            port=22,
            team=self.teams["blue_team"],
        )
        db.session.add(self.service)
        db.session.commit()

    def test_host_at_max_length(self):
        # Build a valid hostname at exactly MAX_HOST_LENGTH
        value = "a" * MAX_HOST_LENGTH
        resp = self.client.post(
            "/api/service/update_host",
            data={"pk": self.service.id, "name": "host", "value": value},
        )
        assert resp.json.get("status") == "Updated Service Information"

    def test_host_exceeds_max_length(self):
        value = "a" * (MAX_HOST_LENGTH + 1)
        resp = self.client.post(
            "/api/service/update_host",
            data={"pk": self.service.id, "name": "host", "value": value},
        )
        assert "error" in resp.json
        assert str(MAX_HOST_LENGTH) in resp.json["error"]
