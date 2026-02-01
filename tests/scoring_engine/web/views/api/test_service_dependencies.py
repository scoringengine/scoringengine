"""Tests for service dependency API endpoints."""
import json
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.web import create_app
from tests.scoring_engine.unit_test import UnitTest


class TestServiceDependencies(UnitTest):

    def setup_method(self):
        super().setup_method()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

        # Create white team and user for auth
        self.white_team = Team(name="White Team", color="White")
        self.session.add(self.white_team)
        self.white_user = User(username="admin", password="testpass", team=self.white_team)
        self.session.add(self.white_user)

        # Create blue team and services
        self.blue_team = Team(name="Blue Team 1", color="Blue")
        self.session.add(self.blue_team)
        self.dns_service = Service(
            name="DNS", team=self.blue_team, check_name="DNS Check", host="10.0.0.1"
        )
        self.http_service = Service(
            name="HTTP", team=self.blue_team, check_name="HTTP Check", host="10.0.0.2"
        )
        self.smtp_service = Service(
            name="SMTP", team=self.blue_team, check_name="SMTP Check", host="10.0.0.3"
        )
        self.session.add(self.dns_service)
        self.session.add(self.http_service)
        self.session.add(self.smtp_service)
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

    def test_get_dependency_requires_auth(self):
        """Test that getting dependency info requires authentication."""
        response = self.client.get(f"/api/admin/service/{self.http_service.id}/dependency")
        assert response.status_code == 302  # Redirect to login

    def test_get_dependency_no_parent(self):
        """Test getting dependency info for service with no parent."""
        self.login("admin", "testpass")
        response = self.client.get(f"/api/admin/service/{self.http_service.id}/dependency")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["service_id"] == self.http_service.id
        assert data["parent_id"] is None
        assert data["parent_name"] is None
        assert data["children"] == []
        assert data["dependency_chain"] == []

    def test_get_dependency_with_parent(self):
        """Test getting dependency info for service with parent."""
        self.http_service.parent = self.dns_service
        self.session.commit()

        self.login("admin", "testpass")
        response = self.client.get(f"/api/admin/service/{self.http_service.id}/dependency")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["parent_id"] == self.dns_service.id
        assert data["parent_name"] == "DNS"
        assert len(data["dependency_chain"]) == 1

    def test_get_dependency_service_not_found(self):
        """Test getting dependency for non-existent service."""
        self.login("admin", "testpass")
        response = self.client.get("/api/admin/service/99999/dependency")
        assert response.status_code == 404

    def test_set_dependency(self):
        """Test setting a parent dependency."""
        self.login("admin", "testpass")
        response = self.client.post(
            f"/api/admin/service/{self.http_service.id}/dependency",
            json={"parent_id": self.dns_service.id},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["parent_id"] == self.dns_service.id

        # Verify in database
        self.session.refresh(self.http_service)
        assert self.http_service.parent_id == self.dns_service.id

    def test_set_dependency_requires_auth(self):
        """Test that setting dependency requires authentication."""
        response = self.client.post(
            f"/api/admin/service/{self.http_service.id}/dependency",
            json={"parent_id": self.dns_service.id},
        )
        assert response.status_code == 302

    def test_set_dependency_clear_parent(self):
        """Test clearing parent dependency with empty value."""
        self.http_service.parent = self.dns_service
        self.session.commit()

        self.login("admin", "testpass")
        response = self.client.post(
            f"/api/admin/service/{self.http_service.id}/dependency",
            json={"parent_id": ""},
        )
        assert response.status_code == 200

        self.session.refresh(self.http_service)
        assert self.http_service.parent_id is None

    def test_set_dependency_prevents_self_reference(self):
        """Test that service cannot be its own parent."""
        self.login("admin", "testpass")
        response = self.client.post(
            f"/api/admin/service/{self.http_service.id}/dependency",
            json={"parent_id": self.http_service.id},
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "own parent" in data["error"]

    def test_set_dependency_prevents_circular(self):
        """Test that circular dependencies are prevented."""
        # Set DNS → HTTP
        self.dns_service.parent = self.http_service
        self.session.commit()

        # Try to set HTTP → DNS (would create circular)
        self.login("admin", "testpass")
        response = self.client.post(
            f"/api/admin/service/{self.http_service.id}/dependency",
            json={"parent_id": self.dns_service.id},
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "circular" in data["error"].lower()

    def test_set_dependency_requires_same_team(self):
        """Test that parent must be from same team."""
        other_team = Team(name="Blue Team 2", color="Blue")
        self.session.add(other_team)
        other_service = Service(
            name="Other DNS", team=other_team, check_name="DNS Check", host="10.0.1.1"
        )
        self.session.add(other_service)
        self.session.commit()

        self.login("admin", "testpass")
        response = self.client.post(
            f"/api/admin/service/{self.http_service.id}/dependency",
            json={"parent_id": other_service.id},
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "same team" in data["error"].lower()

    def test_set_dependency_parent_not_found(self):
        """Test setting non-existent parent."""
        self.login("admin", "testpass")
        response = self.client.post(
            f"/api/admin/service/{self.http_service.id}/dependency",
            json={"parent_id": 99999},
        )
        assert response.status_code == 404

    def test_remove_dependency(self):
        """Test removing parent dependency."""
        self.http_service.parent = self.dns_service
        self.session.commit()

        self.login("admin", "testpass")
        response = self.client.delete(
            f"/api/admin/service/{self.http_service.id}/dependency"
        )
        assert response.status_code == 200

        self.session.refresh(self.http_service)
        assert self.http_service.parent_id is None

    def test_get_team_dependencies(self):
        """Test getting all service dependencies for a team."""
        # Set up some dependencies
        self.http_service.parent = self.dns_service
        self.smtp_service.parent = self.dns_service
        self.session.commit()

        self.login("admin", "testpass")
        response = self.client.get(
            f"/api/admin/team/{self.blue_team.id}/services/dependencies"
        )
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["team_id"] == self.blue_team.id
        assert len(data["services"]) == 3

        # Find HTTP service in response
        http_data = next(s for s in data["services"] if s["name"] == "HTTP")
        assert http_data["parent_id"] == self.dns_service.id
        assert http_data["parent_name"] == "DNS"

        # Find DNS service - should have 2 children
        dns_data = next(s for s in data["services"] if s["name"] == "DNS")
        assert len(dns_data["children_ids"]) == 2

    def test_get_team_dependencies_team_not_found(self):
        """Test getting dependencies for non-existent team."""
        self.login("admin", "testpass")
        response = self.client.get("/api/admin/team/99999/services/dependencies")
        assert response.status_code == 404

    def test_dependency_status_with_failing_parent(self):
        """Test dependency status shows root cause when parent fails."""
        # Set up dependency
        self.http_service.parent = self.dns_service
        self.session.commit()

        # Create failing check for DNS
        round_obj = Round(number=1)
        self.session.add(round_obj)
        check = Check(round=round_obj, service=self.dns_service, result=False, output="Failed")
        self.session.add(check)
        self.session.commit()

        self.login("admin", "testpass")
        response = self.client.get(f"/api/admin/service/{self.http_service.id}/dependency")
        assert response.status_code == 200
        data = json.loads(response.data)

        status = data["dependency_status"]
        assert status["parent_is_down"] is True
        assert status["root_cause"]["id"] == self.dns_service.id
        assert status["root_cause"]["name"] == "DNS"
