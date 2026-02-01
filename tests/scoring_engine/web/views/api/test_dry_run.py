"""Tests for the check dry-run API endpoint."""
import json
from unittest.mock import patch, MagicMock

from scoring_engine.models.environment import Environment
from scoring_engine.models.property import Property
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.web import create_app
from tests.scoring_engine.unit_test import UnitTest


class TestCheckDryRun(UnitTest):
    def setup_method(self):
        super(TestCheckDryRun, self).setup_method()
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

        # Create a service with environment
        self.service = Service(
            name="TestSSH",
            check_name="SSHCheck",
            host="192.168.1.1",
            port=22,
            points=100,
            team=self.blue_team,
        )
        self.session.add(self.service)
        self.session.commit()

        self.environment = Environment(
            service=self.service,
            matching_content=".*SSH.*",
        )
        self.session.add(self.environment)
        self.session.commit()

        # Add required properties for SSHCheck
        prop_user = Property(
            name="username",
            value="testuser",
            environment=self.environment,
        )
        prop_pass = Property(
            name="password",
            value="testpass",
            environment=self.environment,
        )
        self.session.add_all([prop_user, prop_pass])
        self.session.commit()

    def teardown_method(self):
        self.ctx.pop()
        super(TestCheckDryRun, self).teardown_method()

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

    def test_dry_run_requires_authentication(self):
        """Test that dry-run endpoint requires login."""
        resp = self.client.post(
            "/api/admin/check/dry_run",
            json={"service_id": self.service.id},
        )
        # Should redirect to login
        assert resp.status_code in [302, 401]

    def test_dry_run_requires_white_team(self):
        """Test that only white team can run dry-run checks."""
        self.login_blue_team()
        resp = self.client.post(
            "/api/admin/check/dry_run",
            json={"service_id": self.service.id},
        )
        assert resp.status_code == 403
        data = json.loads(resp.data)
        assert data["status"] == "Unauthorized"

    def test_dry_run_requires_service_id(self):
        """Test that service_id is required."""
        self.login_white_team()
        resp = self.client.post(
            "/api/admin/check/dry_run",
            json={},
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "service_id is required" in data["message"]

    def test_dry_run_service_not_found(self):
        """Test error when service doesn't exist."""
        self.login_white_team()
        resp = self.client.post(
            "/api/admin/check/dry_run",
            json={"service_id": 99999},
        )
        assert resp.status_code == 404
        data = json.loads(resp.data)
        assert "not found" in data["message"]

    @patch(
        "scoring_engine.web.views.api.admin._execute_check_sync"
    )
    @patch("scoring_engine.web.views.api.admin._get_check_classes")
    def test_dry_run_success(self, mock_get_checks, mock_execute):
        """Test successful dry-run with passing check."""
        # Mock check class
        mock_check_class = MagicMock()
        mock_check_instance = MagicMock()
        mock_check_instance.command.return_value = "ssh test"
        mock_check_class.return_value = mock_check_instance
        mock_get_checks.return_value = {"SSHCheck": mock_check_class}

        # Mock execution result - output matches matching_content
        mock_execute.return_value = {
            "output": "SSH-2.0-OpenSSH_8.2p1",
            "errored_out": False,
            "execution_time_ms": 150,
        }

        self.login_white_team()
        resp = self.client.post(
            "/api/admin/check/dry_run",
            json={"service_id": self.service.id},
        )

        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["status"] == "success"
        assert data["result"] is True
        assert data["reason"] == "Check Finished Successfully"
        assert "SSH" in data["output"]
        assert data["service_name"] == "TestSSH"
        assert data["team_name"] == "Blue Team 1"
        assert data["execution_time_ms"] == 150

    @patch(
        "scoring_engine.web.views.api.admin._execute_check_sync"
    )
    @patch("scoring_engine.web.views.api.admin._get_check_classes")
    def test_dry_run_failure_wrong_content(
        self, mock_get_checks, mock_execute
    ):
        """Test dry-run with failing check (wrong content)."""
        mock_check_class = MagicMock()
        mock_check_instance = MagicMock()
        mock_check_instance.command.return_value = "ssh test"
        mock_check_class.return_value = mock_check_instance
        mock_get_checks.return_value = {"SSHCheck": mock_check_class}

        # Output doesn't match matching_content (.*SSH.*)
        mock_execute.return_value = {
            "output": "Connection refused",
            "errored_out": False,
            "execution_time_ms": 50,
        }

        self.login_white_team()
        resp = self.client.post(
            "/api/admin/check/dry_run",
            json={"service_id": self.service.id},
        )

        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["status"] == "success"
        assert data["result"] is False
        assert data["reason"] == "Check Received Incorrect Content"

    @patch(
        "scoring_engine.web.views.api.admin._execute_check_sync"
    )
    @patch("scoring_engine.web.views.api.admin._get_check_classes")
    def test_dry_run_timeout(self, mock_get_checks, mock_execute):
        """Test dry-run with timed out check."""
        mock_check_class = MagicMock()
        mock_check_instance = MagicMock()
        mock_check_instance.command.return_value = "ssh test"
        mock_check_class.return_value = mock_check_instance
        mock_get_checks.return_value = {"SSHCheck": mock_check_class}

        mock_execute.return_value = {
            "output": "Check timed out",
            "errored_out": True,
            "execution_time_ms": 30000,
        }

        self.login_white_team()
        resp = self.client.post(
            "/api/admin/check/dry_run",
            json={"service_id": self.service.id},
        )

        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["status"] == "success"
        assert data["result"] is False
        assert data["reason"] == "Check Timed Out"

    @patch("scoring_engine.web.views.api.admin._get_check_classes")
    def test_dry_run_check_class_not_found(self, mock_get_checks):
        """Test error when check class doesn't exist."""
        mock_get_checks.return_value = {}  # No check classes

        self.login_white_team()
        resp = self.client.post(
            "/api/admin/check/dry_run",
            json={"service_id": self.service.id},
        )

        assert resp.status_code == 404
        data = json.loads(resp.data)
        assert "Check class" in data["message"]
        assert "not found" in data["message"]

    def test_dry_run_with_specific_environment(self):
        """Test dry-run with specific environment_id."""
        # Create second environment
        env2 = Environment(
            service=self.service,
            matching_content=".*different.*",
        )
        self.session.add(env2)
        self.session.commit()
        prop_user2 = Property(
            name="username", value="user2", environment=env2
        )
        prop_pass2 = Property(
            name="password", value="pass2", environment=env2
        )
        self.session.add_all([prop_user2, prop_pass2])
        self.session.commit()

        with patch(
            "scoring_engine.web.views.api.admin._get_check_classes"
        ) as mock_get_checks, patch(
            "scoring_engine.web.views.api.admin._execute_check_sync"
        ) as mock_execute:
            mock_check_class = MagicMock()
            mock_check_instance = MagicMock()
            mock_check_instance.command.return_value = "test cmd"
            mock_check_class.return_value = mock_check_instance
            mock_get_checks.return_value = {"SSHCheck": mock_check_class}

            mock_execute.return_value = {
                "output": "different output here",
                "errored_out": False,
                "execution_time_ms": 100,
            }

            self.login_white_team()
            resp = self.client.post(
                "/api/admin/check/dry_run",
                json={
                    "service_id": self.service.id,
                    "environment_id": env2.id,
                },
            )

            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert data["environment_id"] == env2.id
            assert data["matching_content"] == ".*different.*"
            # Should pass because "different" matches
            assert data["result"] is True
