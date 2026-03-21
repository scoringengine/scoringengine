"""Tests for Service API endpoints (update_account, update_host, update_port)."""

from unittest.mock import patch

import pytest

from scoring_engine.db import db
from scoring_engine.models.account import Account
from scoring_engine.models.environment import Environment
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting


class TestUpdateServiceAccount:
    """Tests for POST /api/service/update_account."""

    @pytest.fixture(autouse=True)
    def setup(self, test_client, three_teams):
        self.client = test_client
        self.teams = three_teams
        self.blue_team = three_teams["blue_team"]
        self.white_team = three_teams["white_team"]
        self.red_team = three_teams["red_team"]

        # Create a service with an account for the blue team
        self.service = Service(
            name="TestSSH", check_name="SSH Check", host="10.0.0.1", team=self.blue_team
        )
        db.session.add(self.service)
        db.session.flush()
        self.account = Account(username="admin", password="secret", service_id=self.service.id)
        db.session.add(self.account)
        db.session.commit()

    def login(self, username):
        self.client.post("/login", data={"username": username, "password": "testpass"}, follow_redirects=True)

    def test_requires_auth(self):
        resp = self.client.post("/api/service/update_account")
        assert resp.status_code == 302

    def test_red_team_denied(self):
        self.login("reduser")
        resp = self.client.post(
            "/api/service/update_account",
            data={"pk": self.account.id, "name": "username", "value": "newuser"},
        )
        assert resp.json["error"] == "Incorrect permissions"

    def test_blue_team_update_username(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_account",
            data={"pk": self.account.id, "name": "username", "value": "newuser"},
        )
        assert resp.json["status"] == "Updated Account Information"
        db.session.refresh(self.account)
        assert self.account.username == "newuser"

    def test_blue_team_update_password(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_account",
            data={"pk": self.account.id, "name": "password", "value": "newpass123"},
        )
        assert resp.json["status"] == "Updated Account Information"
        db.session.refresh(self.account)
        assert self.account.password == "newpass123"

    def test_white_team_update_username(self):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/service/update_account",
            data={"pk": self.account.id, "name": "username", "value": "whitechanged"},
        )
        assert resp.json["status"] == "Updated Account Information"

    def test_blue_team_denied_when_username_update_disabled(self):
        setting = Setting.get_setting("blue_team_update_account_usernames")
        setting.value = False
        db.session.commit()
        Setting.clear_cache("blue_team_update_account_usernames")

        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_account",
            data={"pk": self.account.id, "name": "username", "value": "blocked"},
        )
        assert resp.json["error"] == "Incorrect permissions"

    def test_blue_team_denied_when_password_update_disabled(self):
        setting = Setting.get_setting("blue_team_update_account_passwords")
        setting.value = False
        db.session.commit()
        Setting.clear_cache("blue_team_update_account_passwords")

        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_account",
            data={"pk": self.account.id, "name": "password", "value": "blocked"},
        )
        assert resp.json["error"] == "Incorrect permissions"

    def test_white_team_bypasses_disabled_settings(self):
        """White team can update even when blue team settings are disabled."""
        setting = Setting.get_setting("blue_team_update_account_usernames")
        setting.value = False
        db.session.commit()
        Setting.clear_cache("blue_team_update_account_usernames")

        self.login("whiteuser")
        resp = self.client.post(
            "/api/service/update_account",
            data={"pk": self.account.id, "name": "username", "value": "allowed"},
        )
        assert resp.json["status"] == "Updated Account Information"

    def test_invalid_characters_rejected(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_account",
            data={"pk": self.account.id, "name": "username", "value": "bad<>chars"},
        )
        assert "Invalid characters" in resp.json["error"]

    def test_value_with_leading_space_rejected(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_account",
            data={"pk": self.account.id, "name": "username", "value": " leading"},
        )
        assert "Invalid characters" in resp.json["error"]

    def test_value_with_trailing_space_rejected(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_account",
            data={"pk": self.account.id, "name": "username", "value": "trailing "},
        )
        assert "Invalid characters" in resp.json["error"]

    def test_missing_form_fields(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_account",
            data={"pk": self.account.id, "name": "username"},
        )
        assert resp.json["error"] == "Incorrect permissions"

    def test_blue_team_cannot_update_other_teams_account(self):
        """Blue team cannot modify another team's service account."""
        other_service = Service(
            name="OtherSSH", check_name="SSH Check", host="10.0.0.2", team=self.white_team
        )
        db.session.add(other_service)
        db.session.flush()
        other_account = Account(username="other", password="pass", service_id=other_service.id)
        db.session.add(other_account)
        db.session.commit()

        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_account",
            data={"pk": other_account.id, "name": "username", "value": "hacked"},
        )
        assert resp.json["error"] == "Incorrect permissions"

    def test_nonexistent_account(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_account",
            data={"pk": 99999, "name": "username", "value": "noexist"},
        )
        assert resp.json["error"] == "Incorrect permissions"

    def test_xss_escaped_in_username(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_account",
            data={"pk": self.account.id, "name": "username", "value": "user(test)"},
        )
        assert resp.json["status"] == "Updated Account Information"


class TestUpdateServiceHost:
    """Tests for POST /api/service/update_host."""

    @pytest.fixture(autouse=True)
    def setup(self, test_client, three_teams):
        self.client = test_client
        self.teams = three_teams
        self.blue_team = three_teams["blue_team"]
        self.white_team = three_teams["white_team"]

        self.service = Service(
            name="TestHTTP", check_name="HTTP Check", host="10.0.0.1", team=self.blue_team
        )
        db.session.add(self.service)
        db.session.commit()

    def login(self, username):
        self.client.post("/login", data={"username": username, "password": "testpass"}, follow_redirects=True)

    def test_requires_auth(self):
        resp = self.client.post("/api/service/update_host")
        assert resp.status_code == 302

    def test_red_team_denied(self):
        self.login("reduser")
        resp = self.client.post(
            "/api/service/update_host",
            data={"pk": self.service.id, "name": "host", "value": "10.0.0.2"},
        )
        assert resp.json["error"] == "Incorrect permissions"

    @patch("scoring_engine.web.views.api.service.update_overview_data")
    @patch("scoring_engine.web.views.api.service.update_services_data")
    @patch("scoring_engine.web.views.api.service.update_service_data")
    def test_blue_team_update_host(self, mock_svc, mock_svcs, mock_overview):
        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_host",
            data={"pk": self.service.id, "name": "host", "value": "10.0.0.2"},
        )
        assert resp.json["status"] == "Updated Service Information"
        db.session.refresh(self.service)
        assert self.service.host == "10.0.0.2"
        mock_overview.assert_called_once()
        mock_svcs.assert_called_once_with(self.blue_team.id)
        mock_svc.assert_called_once_with(self.service.id)

    @patch("scoring_engine.web.views.api.service.update_overview_data")
    @patch("scoring_engine.web.views.api.service.update_services_data")
    @patch("scoring_engine.web.views.api.service.update_service_data")
    def test_white_team_update_host(self, mock_svc, mock_svcs, mock_overview):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/service/update_host",
            data={"pk": self.service.id, "name": "host", "value": "192.168.1.1"},
        )
        assert resp.json["status"] == "Updated Service Information"

    def test_blue_team_denied_when_hostname_update_disabled(self):
        setting = Setting.get_setting("blue_team_update_hostname")
        setting.value = False
        db.session.commit()
        Setting.clear_cache("blue_team_update_hostname")

        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_host",
            data={"pk": self.service.id, "name": "host", "value": "10.0.0.2"},
        )
        assert resp.json["error"] == "Incorrect permissions"

    @patch("scoring_engine.web.views.api.service.update_overview_data")
    @patch("scoring_engine.web.views.api.service.update_services_data")
    @patch("scoring_engine.web.views.api.service.update_service_data")
    def test_white_team_bypasses_disabled_hostname_setting(self, mock_svc, mock_svcs, mock_overview):
        setting = Setting.get_setting("blue_team_update_hostname")
        setting.value = False
        db.session.commit()
        Setting.clear_cache("blue_team_update_hostname")

        self.login("whiteuser")
        resp = self.client.post(
            "/api/service/update_host",
            data={"pk": self.service.id, "name": "host", "value": "10.0.0.99"},
        )
        assert resp.json["status"] == "Updated Service Information"

    def test_invalid_hostname_characters_rejected(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_host",
            data={"pk": self.service.id, "name": "host", "value": "bad host!"},
        )
        assert "Invalid characters" in resp.json["error"]

    def test_wrong_name_field_denied(self):
        """Sending name != 'host' should not update."""
        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_host",
            data={"pk": self.service.id, "name": "nothost", "value": "10.0.0.2"},
        )
        assert resp.json["error"] == "Incorrect permissions"

    def test_blue_team_cannot_update_other_teams_host(self):
        other_service = Service(
            name="OtherHTTP", check_name="HTTP Check", host="10.0.0.5", team=self.white_team
        )
        db.session.add(other_service)
        db.session.commit()

        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_host",
            data={"pk": other_service.id, "name": "host", "value": "10.0.0.6"},
        )
        assert resp.json["error"] == "Incorrect permissions"

    def test_nonexistent_service(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_host",
            data={"pk": 99999, "name": "host", "value": "10.0.0.2"},
        )
        assert resp.json["error"] == "Incorrect permissions"

    def test_missing_form_fields(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_host",
            data={"pk": self.service.id},
        )
        assert resp.json["error"] == "Incorrect permissions"


class TestUpdateServicePort:
    """Tests for POST /api/service/update_port."""

    @pytest.fixture(autouse=True)
    def setup(self, test_client, three_teams):
        self.client = test_client
        self.teams = three_teams
        self.blue_team = three_teams["blue_team"]
        self.white_team = three_teams["white_team"]

        self.service = Service(
            name="TestHTTP", check_name="HTTP Check", host="10.0.0.1", port=80, team=self.blue_team
        )
        db.session.add(self.service)
        db.session.commit()

    def login(self, username):
        self.client.post("/login", data={"username": username, "password": "testpass"}, follow_redirects=True)

    def test_requires_auth(self):
        resp = self.client.post("/api/service/update_port")
        assert resp.status_code == 302

    def test_red_team_denied(self):
        self.login("reduser")
        resp = self.client.post(
            "/api/service/update_port",
            data={"pk": self.service.id, "name": "port", "value": "8080"},
        )
        assert resp.json["error"] == "Incorrect permissions"

    @patch("scoring_engine.web.views.api.service.update_overview_data")
    @patch("scoring_engine.web.views.api.service.update_services_data")
    @patch("scoring_engine.web.views.api.service.update_service_data")
    def test_blue_team_update_port(self, mock_svc, mock_svcs, mock_overview):
        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_port",
            data={"pk": self.service.id, "name": "port", "value": "8080"},
        )
        assert resp.json["status"] == "Updated Service Information"
        db.session.refresh(self.service)
        assert self.service.port == 8080
        mock_overview.assert_called_once()
        mock_svcs.assert_called_once_with(self.blue_team.id)
        mock_svc.assert_called_once_with(self.service.id)

    @patch("scoring_engine.web.views.api.service.update_overview_data")
    @patch("scoring_engine.web.views.api.service.update_services_data")
    @patch("scoring_engine.web.views.api.service.update_service_data")
    def test_white_team_update_port(self, mock_svc, mock_svcs, mock_overview):
        self.login("whiteuser")
        resp = self.client.post(
            "/api/service/update_port",
            data={"pk": self.service.id, "name": "port", "value": "443"},
        )
        assert resp.json["status"] == "Updated Service Information"

    def test_blue_team_denied_when_port_update_disabled(self):
        setting = Setting.get_setting("blue_team_update_port")
        setting.value = False
        db.session.commit()
        Setting.clear_cache("blue_team_update_port")

        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_port",
            data={"pk": self.service.id, "name": "port", "value": "8080"},
        )
        assert resp.json["error"] == "Incorrect permissions"

    @patch("scoring_engine.web.views.api.service.update_overview_data")
    @patch("scoring_engine.web.views.api.service.update_services_data")
    @patch("scoring_engine.web.views.api.service.update_service_data")
    def test_white_team_bypasses_disabled_port_setting(self, mock_svc, mock_svcs, mock_overview):
        setting = Setting.get_setting("blue_team_update_port")
        setting.value = False
        db.session.commit()
        Setting.clear_cache("blue_team_update_port")

        self.login("whiteuser")
        resp = self.client.post(
            "/api/service/update_port",
            data={"pk": self.service.id, "name": "port", "value": "9090"},
        )
        assert resp.json["status"] == "Updated Service Information"

    def test_non_numeric_port_rejected(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_port",
            data={"pk": self.service.id, "name": "port", "value": "abc"},
        )
        assert "Invalid input" in resp.json["error"] or "Port must be a number" in resp.json["error"]

    def test_wrong_name_field_denied(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_port",
            data={"pk": self.service.id, "name": "notport", "value": "8080"},
        )
        assert resp.json["error"] == "Incorrect permissions"

    def test_blue_team_cannot_update_other_teams_port(self):
        other_service = Service(
            name="OtherHTTP", check_name="HTTP Check", host="10.0.0.5", port=80, team=self.white_team
        )
        db.session.add(other_service)
        db.session.commit()

        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_port",
            data={"pk": other_service.id, "name": "port", "value": "9999"},
        )
        assert resp.json["error"] == "Incorrect permissions"

    def test_nonexistent_service(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_port",
            data={"pk": 99999, "name": "port", "value": "8080"},
        )
        assert resp.json["error"] == "Incorrect permissions"

    def test_missing_form_fields(self):
        self.login("blueuser")
        resp = self.client.post(
            "/api/service/update_port",
            data={"pk": self.service.id},
        )
        assert resp.json["error"] == "Incorrect permissions"
