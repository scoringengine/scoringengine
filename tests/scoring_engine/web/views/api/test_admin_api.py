"""Comprehensive tests for Admin API endpoints"""
import html
from unittest.mock import MagicMock, patch

from scoring_engine.models.check import Check
from scoring_engine.models.environment import Environment
from scoring_engine.models.property import Property
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.web import create_app
from tests.scoring_engine.unit_test import UnitTest


class TestAdminAPI(UnitTest):
    """Comprehensive security and functionality tests for Admin API"""

    def setup_method(self):
        super(TestAdminAPI, self).setup_method()
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        # Create teams
        self.white_team = Team(name="White Team", color="White")
        self.blue_team = Team(name="Blue Team", color="Blue")
        self.red_team = Team(name="Red Team", color="Red")

        self.session.add_all([self.white_team, self.blue_team, self.red_team])
        self.session.commit()

        # Create users
        self.white_user = User(username="whiteuser", password="pass", team=self.white_team)
        self.blue_user = User(username="blueuser", password="pass", team=self.blue_team)
        self.red_user = User(username="reduser", password="pass", team=self.red_team)

        self.session.add_all([self.white_user, self.blue_user, self.red_user])
        self.session.commit()

    def teardown_method(self):
        self.ctx.pop()
        super(TestAdminAPI, self).teardown_method()

    def login(self, username, password):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    def logout(self):
        return self.client.get("/logout", follow_redirects=True)

    # Authorization Tests
    def test_admin_update_environment_requires_auth(self):
        """Test that admin endpoints require authentication"""
        resp = self.client.post("/api/admin/update_environment_info")
        assert resp.status_code == 302
        assert "/login?" in resp.location

    def test_admin_update_environment_requires_white_team(self):
        """Test that only white team can update environment"""
        service = Service(
            name="Test",
            check_name="ICMP IPv4 Check",
            host="1.2.3.4",
            team=self.blue_team
        )
        env = Environment(service=service, matching_content="test")
        self.session.add_all([service, env])
        self.session.commit()

        # Try as blue team
        self.login("blueuser", "pass")
        resp = self.client.post(
            "/api/admin/update_environment_info",
            data={"pk": env.id, "name": "matching_content", "value": "new"}
        )

        assert resp.status_code == 200
        assert resp.json["error"] == "Incorrect permissions"

        # Try as red team
        self.logout()
        self.login("reduser", "pass")
        resp = self.client.post(
            "/api/admin/update_environment_info",
            data={"pk": env.id, "name": "matching_content", "value": "new"}
        )

        assert resp.status_code == 200
        assert resp.json["error"] == "Incorrect permissions"

    def test_admin_update_environment_xss_protection(self):
        """SECURITY: Test that environment updates are protected against XSS"""
        service = Service(
            name="Test",
            check_name="ICMP IPv4 Check",
            host="1.2.3.4",
            team=self.blue_team
        )
        env = Environment(service=service, matching_content="test")
        self.session.add_all([service, env])
        self.session.commit()

        self.login("whiteuser", "pass")

        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror='alert(1)'>",
            "javascript:alert('XSS')",
            "<svg onload=alert(1)>",
            "';alert(String.fromCharCode(88,83,83))//'"
        ]

        for payload in xss_payloads:
            resp = self.client.post(
                "/api/admin/update_environment_info",
                data={"pk": env.id, "name": "matching_content", "value": payload}
            )

            assert resp.status_code == 200
            self.session.refresh(env)

            # Value should be HTML-escaped
            assert env.matching_content == html.escape(payload)
            assert "<script>" not in env.matching_content
            # Verify dangerous characters are escaped
            if "<" in payload:
                assert "<" not in env.matching_content or env.matching_content == payload
                assert "&lt;" in env.matching_content or "<" not in payload

    def test_admin_update_environment_validates_fields(self):
        """Test that environment update validates required fields"""
        self.login("whiteuser", "pass")

        # Missing 'value'
        resp = self.client.post(
            "/api/admin/update_environment_info",
            data={"pk": 1, "name": "matching_content"}
        )
        assert resp.json.get("error") == "Incorrect permissions"

        # Missing 'name'
        resp = self.client.post(
            "/api/admin/update_environment_info",
            data={"pk": 1, "value": "test"}
        )
        assert resp.json.get("error") == "Incorrect permissions"

        # Missing 'pk'
        resp = self.client.post(
            "/api/admin/update_environment_info",
            data={"name": "matching_content", "value": "test"}
        )
        assert resp.json.get("error") == "Incorrect permissions"

    def test_admin_update_environment_success(self):
        """Test successful environment update"""
        service = Service(
            name="Test",
            check_name="ICMP IPv4 Check",
            host="1.2.3.4",
            team=self.blue_team
        )
        env = Environment(service=service, matching_content="old_value")
        self.session.add_all([service, env])
        self.session.commit()

        self.login("whiteuser", "pass")
        resp = self.client.post(
            "/api/admin/update_environment_info",
            data={"pk": env.id, "name": "matching_content", "value": "new_value"}
        )

        assert resp.status_code == 200
        assert resp.json["status"] == "Updated Environment Information"

        self.session.refresh(env)
        assert env.matching_content == "new_value"

    # Property Update Tests
    def test_admin_update_property_requires_white_team(self):
        """Test that only white team can update properties"""
        service = Service(
            name="Test",
            check_name="ICMP IPv4 Check",
            host="1.2.3.4",
            team=self.blue_team
        )
        env = Environment(service=service, matching_content="test")
        self.session.add_all([service, env])
        self.session.commit()

        prop = Property(name="key", value="value", environment_id=env.id)
        self.session.add(prop)
        self.session.commit()
        self.session.add_all([service, prop])
        self.session.commit()

        # Try as blue team
        self.login("blueuser", "pass")
        resp = self.client.post(
            "/api/admin/update_property",
            data={"pk": prop.id, "name": "property_name", "value": "new"}
        )

        assert resp.json["error"] == "Incorrect permissions"

    def test_admin_update_property_xss_protection(self):
        """SECURITY: Test that property updates are protected against XSS"""
        service = Service(
            name="Test",
            check_name="ICMP IPv4 Check",
            host="1.2.3.4",
            team=self.blue_team
        )
        env = Environment(service=service, matching_content="test")
        self.session.add_all([service, env])
        self.session.commit()

        prop = Property(name="key", value="value", environment_id=env.id)
        self.session.add(prop)
        self.session.commit()
        self.session.add_all([service, prop])
        self.session.commit()

        self.login("whiteuser", "pass")

        # Test XSS in property name
        resp = self.client.post(
            "/api/admin/update_property",
            data={
                "pk": prop.id,
                "name": "property_name",
                "value": "<script>alert('xss')</script>"
            }
        )

        assert resp.status_code == 200
        self.session.refresh(prop)
        assert prop.name == html.escape("<script>alert('xss')</script>")

        # Test XSS in property value
        resp = self.client.post(
            "/api/admin/update_property",
            data={
                "pk": prop.id,
                "name": "property_value",
                "value": "<img src=x onerror=alert(1)>"
            }
        )

        assert resp.status_code == 200
        self.session.refresh(prop)
        assert prop.value == html.escape("<img src=x onerror=alert(1)>")

    def test_admin_update_property_both_fields(self):
        """Test updating both property name and value"""
        service = Service(
            name="Test",
            check_name="ICMP IPv4 Check",
            host="1.2.3.4",
            team=self.blue_team
        )
        env = Environment(service=service, matching_content="test")
        self.session.add_all([service, env])
        self.session.commit()

        prop = Property(name="old_key", value="old_value", environment_id=env.id)
        self.session.add(prop)
        self.session.commit()
        self.session.add_all([service, prop])
        self.session.commit()

        self.login("whiteuser", "pass")

        # Update name
        resp = self.client.post(
            "/api/admin/update_property",
            data={"pk": prop.id, "name": "property_name", "value": "new_key"}
        )
        assert resp.status_code == 200
        self.session.refresh(prop)
        assert prop.name == "new_key"

        # Update value
        resp = self.client.post(
            "/api/admin/update_property",
            data={"pk": prop.id, "name": "property_value", "value": "new_value"}
        )
        assert resp.status_code == 200
        self.session.refresh(prop)
        assert prop.value == "new_value"

    # Check Update Tests
    def test_admin_update_check_requires_white_team(self):
        """Test that only white team can update checks"""
        service = Service(
            name="Test",
            check_name="ICMP IPv4 Check",
            host="1.2.3.4",
            team=self.blue_team
        )
        round_obj = Round(number=1)
        check = Check(service=service, round=round_obj, result=True, output="test")
        self.session.add_all([service, round_obj, check])
        self.session.commit()

        # Try as blue team
        self.login("blueuser", "pass")
        resp = self.client.post(
            "/api/admin/update_check",
            data={"pk": check.id, "name": "check_value", "value": "2"}
        )

        assert resp.json["error"] == "Incorrect permissions"

    def test_admin_update_check_result_pass_to_fail(self):
        """Test changing check result from pass to fail"""
        service = Service(
            name="Test",
            check_name="ICMP IPv4 Check",
            host="1.2.3.4",
            team=self.blue_team
        )
        round_obj = Round(number=1)
        check = Check(service=service, round=round_obj, result=True, output="test")
        self.session.add_all([service, round_obj, check])
        self.session.commit()

        self.login("whiteuser", "pass")

        with patch("scoring_engine.web.views.api.admin.update_scoreboard_data"):
            with patch("scoring_engine.web.views.api.admin.update_overview_data"):
                resp = self.client.post(
                    "/api/admin/update_check",
                    data={"pk": check.id, "name": "check_value", "value": "2"}
                )

        assert resp.status_code == 200
        self.session.refresh(check)
        assert check.result is False

    def test_admin_update_check_result_fail_to_pass(self):
        """Test changing check result from fail to pass"""
        service = Service(
            name="Test",
            check_name="ICMP IPv4 Check",
            host="1.2.3.4",
            team=self.blue_team
        )
        round_obj = Round(number=1)
        check = Check(service=service, round=round_obj, result=False, output="test")
        self.session.add_all([service, round_obj, check])
        self.session.commit()

        self.login("whiteuser", "pass")

        with patch("scoring_engine.web.views.api.admin.update_scoreboard_data"):
            with patch("scoring_engine.web.views.api.admin.update_overview_data"):
                resp = self.client.post(
                    "/api/admin/update_check",
                    data={"pk": check.id, "name": "check_value", "value": "1"}
                )

        assert resp.status_code == 200
        self.session.refresh(check)
        assert check.result is True

    def test_admin_update_check_reason(self):
        """Test updating check reason/output"""
        service = Service(
            name="Test",
            check_name="ICMP IPv4 Check",
            host="1.2.3.4",
            team=self.blue_team
        )
        round_obj = Round(number=1)
        check = Check(service=service, round=round_obj, result=True, output="old", reason="old_reason")
        self.session.add_all([service, round_obj, check])
        self.session.commit()

        self.login("whiteuser", "pass")

        with patch("scoring_engine.web.views.api.admin.update_scoreboard_data"):
            with patch("scoring_engine.web.views.api.admin.update_overview_data"):
                resp = self.client.post(
                    "/api/admin/update_check",
                    data={"pk": check.id, "name": "check_reason", "value": "new_reason"}
                )

        assert resp.status_code == 200
        self.session.refresh(check)
        assert check.reason == "new_reason"

    def test_admin_update_check_triggers_cache_update(self):
        """Test that updating check triggers cache updates"""
        service = Service(
            name="Test",
            check_name="ICMP IPv4 Check",
            host="1.2.3.4",
            team=self.blue_team
        )
        round_obj = Round(number=1)
        check = Check(service=service, round=round_obj, result=True, output="test")
        self.session.add_all([service, round_obj, check])
        self.session.commit()

        self.login("whiteuser", "pass")

        with patch("scoring_engine.web.views.api.admin.update_scoreboard_data") as mock_scoreboard:
            with patch("scoring_engine.web.views.api.admin.update_overview_data") as mock_overview:
                resp = self.client.post(
                    "/api/admin/update_check",
                    data={"pk": check.id, "name": "check_value", "value": "2"}
                )

                # Cache updates should be called
                mock_scoreboard.assert_called_once()
                mock_overview.assert_called_once()

    def test_admin_update_check_invalid_value(self):
        """Test that invalid check values are handled"""
        service = Service(
            name="Test",
            check_name="ICMP IPv4 Check",
            host="1.2.3.4",
            team=self.blue_team
        )
        round_obj = Round(number=1)
        check = Check(service=service, round=round_obj, result=True, output="test")
        self.session.add_all([service, round_obj, check])
        self.session.commit()

        self.login("whiteuser", "pass")

        # Invalid value (not 1 or 2)
        with patch("scoring_engine.web.views.api.admin.update_scoreboard_data"):
            with patch("scoring_engine.web.views.api.admin.update_overview_data"):
                resp = self.client.post(
                    "/api/admin/update_check",
                    data={"pk": check.id, "name": "check_value", "value": "3"}
                )

        # Should not crash, just not update
        self.session.refresh(check)
        assert check.result is True  # Unchanged

    # Password Update Tests
    def test_admin_update_password_requires_auth(self):
        """Test that password update requires authentication"""
        resp = self.client.post("/api/admin/update_password")
        assert resp.status_code == 302

    def test_admin_add_user_requires_auth(self):
        """Test that add user requires authentication"""
        resp = self.client.post("/api/admin/add_user")
        assert resp.status_code == 302

    # Round Progress Test
    def test_admin_get_round_progress_requires_auth(self):
        """Test that get round progress requires authentication"""
        resp = self.client.get("/api/admin/get_round_progress")
        assert resp.status_code == 302

    # Teams Test
    def test_admin_get_teams_requires_auth(self):
        """Test that get teams requires authentication"""
        resp = self.client.get("/api/admin/get_teams")
        assert resp.status_code == 302

    # SQL Injection Tests
    def test_admin_update_environment_sql_injection_prevention(self):
        """SECURITY: Test SQL injection prevention in environment updates"""
        service = Service(
            name="Test",
            check_name="ICMP IPv4 Check",
            host="1.2.3.4",
            team=self.blue_team
        )
        env = Environment(service=service, matching_content="test")
        self.session.add_all([service, env])
        self.session.commit()

        self.login("whiteuser", "pass")

        sql_injections = [
            "'; DROP TABLE environment; --",
            "1' OR '1'='1",
            "' UNION SELECT password FROM users--",
        ]

        for injection in sql_injections:
            resp = self.client.post(
                "/api/admin/update_environment_info",
                data={"pk": env.id, "name": "matching_content", "value": injection}
            )

            assert resp.status_code == 200
            self.session.refresh(env)

            # Value should be escaped
            assert env.matching_content == html.escape(injection)

    def test_admin_update_property_sql_injection_prevention(self):
        """SECURITY: Test SQL injection prevention in property updates"""
        service = Service(
            name="Test",
            check_name="ICMP IPv4 Check",
            host="1.2.3.4",
            team=self.blue_team
        )
        env = Environment(service=service, matching_content="test")
        self.session.add_all([service, env])
        self.session.commit()

        prop = Property(name="key", value="value", environment_id=env.id)
        self.session.add(prop)
        self.session.commit()
        self.session.add_all([service, prop])
        self.session.commit()

        self.login("whiteuser", "pass")

        sql_injection = "'; DROP TABLE property; --"

        resp = self.client.post(
            "/api/admin/update_property",
            data={"pk": prop.id, "name": "property_value", "value": sql_injection}
        )

        assert resp.status_code == 200
        self.session.refresh(prop)

        # Value should be escaped
        assert prop.value == html.escape(sql_injection)

    def test_admin_nonexistent_environment(self):
        """Test updating nonexistent environment returns error"""
        self.login("whiteuser", "pass")

        resp = self.client.post(
            "/api/admin/update_environment_info",
            data={"pk": 99999, "name": "matching_content", "value": "test"}
        )

        # Should return error for nonexistent environment
        assert "error" in resp.json or resp.json.get("status") != "Updated Environment Information"

    def test_admin_nonexistent_property(self):
        """Test updating nonexistent property returns error"""
        self.login("whiteuser", "pass")

        resp = self.client.post(
            "/api/admin/update_property",
            data={"pk": 99999, "name": "property_name", "value": "test"}
        )

        # Should return error for nonexistent property
        assert "error" in resp.json or resp.json.get("status") != "Updated Property Information"

    def test_admin_nonexistent_check(self):
        """Test updating nonexistent check returns error"""
        self.login("whiteuser", "pass")

        resp = self.client.post(
            "/api/admin/update_check",
            data={"pk": 99999, "name": "check_value", "value": "1"}
        )

        # Should return error for nonexistent check
        assert "error" in resp.json or resp.json.get("status") != "Updated Check Information"
