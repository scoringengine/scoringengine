"""Tests for the check dry-run API endpoint."""
import json
from unittest.mock import patch, MagicMock

import pytest

from scoring_engine.db import db
from scoring_engine.models.environment import Environment
from scoring_engine.models.property import Property
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.models.user import User


def _login(client, username):
    return client.post("/login", data={"username": username, "password": "testpass"}, follow_redirects=True)


class TestCheckDryRun:
    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session):
        self.client = test_client

        self.white_team = Team(name="White Team", color="White")
        self.blue_team = Team(name="Blue Team 1", color="Blue")
        db.session.add_all([self.white_team, self.blue_team])
        db.session.commit()

        self.white_user = User(username="whiteuser", password="testpass", team=self.white_team)
        self.blue_user = User(username="blueuser", password="testpass", team=self.blue_team)
        db.session.add_all([self.white_user, self.blue_user])
        db.session.commit()

        self.service = Service(
            name="TestSSH",
            check_name="SSHCheck",
            host="192.168.1.1",
            port=22,
            points=100,
            team=self.blue_team,
        )
        db.session.add(self.service)
        db.session.commit()

        self.environment = Environment(service=self.service, matching_content=".*SSH.*")
        db.session.add(self.environment)
        db.session.commit()

        prop_user = Property(name="username", value="testuser", environment=self.environment)
        prop_pass = Property(name="password", value="testpass", environment=self.environment)
        db.session.add_all([prop_user, prop_pass])
        db.session.commit()

    def test_dry_run_requires_authentication(self):
        resp = self.client.post("/api/admin/check/dry_run", json={"service_id": self.service.id})
        assert resp.status_code in [302, 401]

    def test_dry_run_requires_white_team(self):
        _login(self.client, "blueuser")
        resp = self.client.post("/api/admin/check/dry_run", json={"service_id": self.service.id})
        assert resp.status_code == 403
        assert resp.json["status"] == "Unauthorized"

    def test_dry_run_requires_service_id(self):
        _login(self.client, "whiteuser")
        resp = self.client.post("/api/admin/check/dry_run", json={})
        assert resp.status_code == 400
        assert "service_id is required" in resp.json["message"]

    def test_dry_run_service_not_found(self):
        _login(self.client, "whiteuser")
        resp = self.client.post("/api/admin/check/dry_run", json={"service_id": 99999})
        assert resp.status_code == 404
        assert "not found" in resp.json["message"]

    @patch("scoring_engine.web.views.api.admin.execute_command")
    @patch("scoring_engine.web.views.api.admin._get_check_classes")
    def test_dry_run_success(self, mock_get_checks, mock_exec_cmd):
        mock_check_class = MagicMock()
        mock_check_instance = MagicMock()
        mock_check_instance.command.return_value = "ssh test"
        mock_check_class.return_value = mock_check_instance
        mock_get_checks.return_value = {"SSHCheck": mock_check_class}

        mock_result = MagicMock()
        mock_result.get.return_value = {"output": "SSH-2.0-OpenSSH_8.2p1", "errored_out": False}
        mock_exec_cmd.apply_async.return_value = mock_result

        _login(self.client, "whiteuser")
        resp = self.client.post("/api/admin/check/dry_run", json={"service_id": self.service.id})

        assert resp.status_code == 200
        data = resp.json
        assert data["status"] == "success"
        assert data["result"] is True
        assert data["reason"] == "Check Finished Successfully"
        assert "SSH" in data["output"]
        assert data["service_name"] == "TestSSH"
        assert data["team_name"] == "Blue Team 1"

    @patch("scoring_engine.web.views.api.admin.execute_command")
    @patch("scoring_engine.web.views.api.admin._get_check_classes")
    def test_dry_run_failure_wrong_content(self, mock_get_checks, mock_exec_cmd):
        mock_check_class = MagicMock()
        mock_check_instance = MagicMock()
        mock_check_instance.command.return_value = "ssh test"
        mock_check_class.return_value = mock_check_instance
        mock_get_checks.return_value = {"SSHCheck": mock_check_class}

        mock_result = MagicMock()
        mock_result.get.return_value = {"output": "Connection refused", "errored_out": False}
        mock_exec_cmd.apply_async.return_value = mock_result

        _login(self.client, "whiteuser")
        resp = self.client.post("/api/admin/check/dry_run", json={"service_id": self.service.id})

        assert resp.status_code == 200
        data = resp.json
        assert data["result"] is False
        assert data["reason"] == "Check Received Incorrect Content"

    @patch("scoring_engine.web.views.api.admin.execute_command")
    @patch("scoring_engine.web.views.api.admin._get_check_classes")
    def test_dry_run_timeout(self, mock_get_checks, mock_exec_cmd):
        mock_check_class = MagicMock()
        mock_check_instance = MagicMock()
        mock_check_instance.command.return_value = "ssh test"
        mock_check_class.return_value = mock_check_instance
        mock_get_checks.return_value = {"SSHCheck": mock_check_class}

        mock_result = MagicMock()
        mock_result.get.return_value = {"output": "Check timed out", "errored_out": True}
        mock_exec_cmd.apply_async.return_value = mock_result

        _login(self.client, "whiteuser")
        resp = self.client.post("/api/admin/check/dry_run", json={"service_id": self.service.id})

        assert resp.status_code == 200
        data = resp.json
        assert data["result"] is False
        assert data["reason"] == "Check Timed Out"

    @patch("scoring_engine.web.views.api.admin._get_check_classes")
    def test_dry_run_check_class_not_found(self, mock_get_checks):
        mock_get_checks.return_value = {}

        _login(self.client, "whiteuser")
        resp = self.client.post("/api/admin/check/dry_run", json={"service_id": self.service.id})

        assert resp.status_code == 404
        assert "Check class" in resp.json["message"]
        assert "not found" in resp.json["message"]

    @patch("scoring_engine.web.views.api.admin.execute_command")
    @patch("scoring_engine.web.views.api.admin._get_check_classes")
    def test_dry_run_with_specific_environment(self, mock_get_checks, mock_exec_cmd):
        env2 = Environment(service=self.service, matching_content=".*different.*")
        db.session.add(env2)
        db.session.commit()
        db.session.add_all([
            Property(name="username", value="user2", environment=env2),
            Property(name="password", value="pass2", environment=env2),
        ])
        db.session.commit()

        mock_check_class = MagicMock()
        mock_check_instance = MagicMock()
        mock_check_instance.command.return_value = "test cmd"
        mock_check_class.return_value = mock_check_instance
        mock_get_checks.return_value = {"SSHCheck": mock_check_class}

        mock_result = MagicMock()
        mock_result.get.return_value = {"output": "different output here", "errored_out": False}
        mock_exec_cmd.apply_async.return_value = mock_result

        _login(self.client, "whiteuser")
        resp = self.client.post(
            "/api/admin/check/dry_run",
            json={"service_id": self.service.id, "environment_id": env2.id},
        )

        assert resp.status_code == 200
        data = resp.json
        assert data["environment_id"] == env2.id
        assert data["matching_content"] == ".*different.*"
        assert data["result"] is True
