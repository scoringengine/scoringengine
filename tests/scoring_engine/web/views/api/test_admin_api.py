"""Comprehensive tests for Admin API endpoints"""

import html
from unittest.mock import MagicMock, patch

import pytest

from scoring_engine.db import db
from scoring_engine.models.check import Check
from scoring_engine.models.environment import Environment
from scoring_engine.models.property import Property
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting

ADMIN_API_AUTH_PATHS = [
    pytest.param("post", "/api/admin/update_environment_info", id="update_environment"),
    pytest.param("post", "/api/admin/update_password", id="update_password"),
    pytest.param("post", "/api/admin/add_user", id="add_user"),
    pytest.param("get", "/api/admin/get_round_progress", id="get_round_progress"),
    pytest.param("get", "/api/admin/get_teams", id="get_teams"),
    pytest.param("post", "/api/admin/toggle_engine", id="toggle_engine"),
    pytest.param("get", "/api/admin/get_engine_paused", id="get_engine_paused"),
]


class TestAdminAPI:
    """Comprehensive security and functionality tests for Admin API"""

    @pytest.fixture(autouse=True)
    def setup(self, test_client, three_teams):
        self.client = test_client
        self.white_team = three_teams["white_team"]
        self.blue_team = three_teams["blue_team"]
        self.red_team = three_teams["red_team"]

    def login(self, username, password="testpass"):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    def logout(self):
        return self.client.get("/logout", follow_redirects=True)

    # Authorization Tests
    @pytest.mark.parametrize("method,path", ADMIN_API_AUTH_PATHS)
    def test_requires_auth(self, method, path):
        """Test that admin endpoints require authentication"""
        resp = getattr(self.client, method)(path)
        assert resp.status_code == 302
        assert "/login?" in resp.location

    def test_admin_update_environment_requires_white_team(self):
        """Test that only white team can update environment"""
        service = Service(name="Test", check_name="ICMP IPv4 Check", host="1.2.3.4", team=self.blue_team)
        env = Environment(service=service, matching_content="test")
        db.session.add_all([service, env])
        db.session.commit()

        # Try as blue team
        self.login("blueuser")
        resp = self.client.post(
            "/api/admin/update_environment_info", data={"pk": env.id, "name": "matching_content", "value": "new"}
        )
        assert resp.status_code == 200
        assert resp.json["error"] == "Incorrect permissions"

        # Try as red team
        self.logout()
        self.login("reduser")
        resp = self.client.post(
            "/api/admin/update_environment_info", data={"pk": env.id, "name": "matching_content", "value": "new"}
        )
        assert resp.status_code == 200
        assert resp.json["error"] == "Incorrect permissions"

    def test_admin_update_environment_xss_protection(self):
        """SECURITY: Test that environment updates are protected against XSS"""
        service = Service(name="Test", check_name="ICMP IPv4 Check", host="1.2.3.4", team=self.blue_team)
        env = Environment(service=service, matching_content="test")
        db.session.add_all([service, env])
        db.session.commit()

        self.login("whiteuser")

        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror='alert(1)'>",
            "javascript:alert('XSS')",
            "<svg onload=alert(1)>",
            "';alert(String.fromCharCode(88,83,83))//'",
        ]

        for payload in xss_payloads:
            resp = self.client.post(
                "/api/admin/update_environment_info", data={"pk": env.id, "name": "matching_content", "value": payload}
            )
            assert resp.status_code == 200
            db.session.refresh(env)

            # Value should be HTML-escaped
            assert env.matching_content == html.escape(payload)
            assert "<script>" not in env.matching_content
            # Verify dangerous characters are escaped
            if "<" in payload:
                assert "<" not in env.matching_content or env.matching_content == payload
                assert "&lt;" in env.matching_content or "<" not in payload

    def test_admin_update_environment_validates_fields(self):
        """Test that environment update validates required fields"""
        self.login("whiteuser")

        # Missing 'value'
        resp = self.client.post("/api/admin/update_environment_info", data={"pk": 1, "name": "matching_content"})
        assert resp.json.get("error") == "Incorrect permissions"

        # Missing 'name'
        resp = self.client.post("/api/admin/update_environment_info", data={"pk": 1, "value": "test"})
        assert resp.json.get("error") == "Incorrect permissions"

        # Missing 'pk'
        resp = self.client.post(
            "/api/admin/update_environment_info", data={"name": "matching_content", "value": "test"}
        )
        assert resp.json.get("error") == "Incorrect permissions"

    def test_admin_update_environment_success(self):
        """Test successful environment update"""
        service = Service(name="Test", check_name="ICMP IPv4 Check", host="1.2.3.4", team=self.blue_team)
        env = Environment(service=service, matching_content="old_value")
        db.session.add_all([service, env])
        db.session.commit()

        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/update_environment_info", data={"pk": env.id, "name": "matching_content", "value": "new_value"}
        )

        assert resp.status_code == 200
        assert resp.json["status"] == "Updated Environment Information"

        db.session.refresh(env)
        assert env.matching_content == "new_value"

    # Property Update Tests
    def test_admin_update_property_requires_white_team(self):
        """Test that only white team can update properties"""
        service = Service(name="Test", check_name="ICMP IPv4 Check", host="1.2.3.4", team=self.blue_team)
        env = Environment(service=service, matching_content="test")
        prop = Property(name="key", value="value", environment=env)
        db.session.add_all([service, env, prop])
        db.session.commit()

        # Try as blue team
        self.login("blueuser")
        resp = self.client.post(
            "/api/admin/update_property", data={"pk": prop.id, "name": "property_name", "value": "new"}
        )
        assert resp.json["error"] == "Incorrect permissions"

    def test_admin_update_property_xss_protection(self):
        """SECURITY: Test that property updates are protected against XSS"""
        service = Service(name="Test", check_name="ICMP IPv4 Check", host="1.2.3.4", team=self.blue_team)
        env = Environment(service=service, matching_content="test")
        prop = Property(name="key", value="value", environment=env)
        db.session.add_all([service, env, prop])
        db.session.commit()

        self.login("whiteuser")

        # Test XSS in property name
        resp = self.client.post(
            "/api/admin/update_property",
            data={"pk": prop.id, "name": "property_name", "value": "<script>alert('xss')</script>"},
        )
        assert resp.status_code == 200
        db.session.refresh(prop)
        assert prop.name == html.escape("<script>alert('xss')</script>")

        # Test XSS in property value
        resp = self.client.post(
            "/api/admin/update_property",
            data={"pk": prop.id, "name": "property_value", "value": "<img src=x onerror=alert(1)>"},
        )
        assert resp.status_code == 200
        db.session.refresh(prop)
        assert prop.value == html.escape("<img src=x onerror=alert(1)>")

    def test_admin_update_property_both_fields(self):
        """Test updating both property name and value"""
        service = Service(name="Test", check_name="ICMP IPv4 Check", host="1.2.3.4", team=self.blue_team)
        env = Environment(service=service, matching_content="test")
        prop = Property(name="old_key", value="old_value", environment=env)
        db.session.add_all([service, env, prop])
        db.session.commit()

        self.login("whiteuser")

        # Update name
        resp = self.client.post(
            "/api/admin/update_property", data={"pk": prop.id, "name": "property_name", "value": "new_key"}
        )
        assert resp.status_code == 200
        db.session.refresh(prop)
        assert prop.name == "new_key"

        # Update value
        resp = self.client.post(
            "/api/admin/update_property", data={"pk": prop.id, "name": "property_value", "value": "new_value"}
        )
        assert resp.status_code == 200
        db.session.refresh(prop)
        assert prop.value == "new_value"

    # Check Update Tests
    def test_admin_update_check_requires_white_team(self):
        """Test that only white team can update checks"""
        service = Service(name="Test", check_name="ICMP IPv4 Check", host="1.2.3.4", team=self.blue_team)
        round_obj = Round(number=1)
        check = Check(service=service, round=round_obj, result=True, output="test")
        db.session.add_all([service, round_obj, check])
        db.session.commit()

        # Try as blue team
        self.login("blueuser")
        resp = self.client.post("/api/admin/update_check", data={"pk": check.id, "name": "check_value", "value": "2"})
        assert resp.json["error"] == "Incorrect permissions"

    def test_admin_update_check_result_pass_to_fail(self):
        """Test changing check result from pass to fail"""
        service = Service(name="Test", check_name="ICMP IPv4 Check", host="1.2.3.4", team=self.blue_team)
        round_obj = Round(number=1)
        check = Check(service=service, round=round_obj, result=True, output="test")
        db.session.add_all([service, round_obj, check])
        db.session.commit()

        self.login("whiteuser")

        with patch("scoring_engine.web.views.api.admin.update_scoreboard_data"):
            with patch("scoring_engine.web.views.api.admin.update_overview_data"):
                resp = self.client.post(
                    "/api/admin/update_check", data={"pk": check.id, "name": "check_value", "value": "2"}
                )

        assert resp.status_code == 200
        db.session.refresh(check)
        assert check.result is False

    def test_admin_update_check_result_fail_to_pass(self):
        """Test changing check result from fail to pass"""
        service = Service(name="Test", check_name="ICMP IPv4 Check", host="1.2.3.4", team=self.blue_team)
        round_obj = Round(number=1)
        check = Check(service=service, round=round_obj, result=False, output="test")
        db.session.add_all([service, round_obj, check])
        db.session.commit()

        self.login("whiteuser")

        with patch("scoring_engine.web.views.api.admin.update_scoreboard_data"):
            with patch("scoring_engine.web.views.api.admin.update_overview_data"):
                resp = self.client.post(
                    "/api/admin/update_check", data={"pk": check.id, "name": "check_value", "value": "1"}
                )

        assert resp.status_code == 200
        db.session.refresh(check)
        assert check.result is True

    def test_admin_update_check_reason(self):
        """Test updating check reason/output"""
        service = Service(name="Test", check_name="ICMP IPv4 Check", host="1.2.3.4", team=self.blue_team)
        round_obj = Round(number=1)
        check = Check(service=service, round=round_obj, result=True, output="old", reason="old_reason")
        db.session.add_all([service, round_obj, check])
        db.session.commit()

        self.login("whiteuser")

        with patch("scoring_engine.web.views.api.admin.update_scoreboard_data"):
            with patch("scoring_engine.web.views.api.admin.update_overview_data"):
                resp = self.client.post(
                    "/api/admin/update_check", data={"pk": check.id, "name": "check_reason", "value": "new_reason"}
                )

        assert resp.status_code == 200
        db.session.refresh(check)
        assert check.reason == "new_reason"

    def test_admin_update_check_triggers_cache_update(self):
        """Test that updating check triggers cache updates"""
        service = Service(name="Test", check_name="ICMP IPv4 Check", host="1.2.3.4", team=self.blue_team)
        round_obj = Round(number=1)
        check = Check(service=service, round=round_obj, result=True, output="test")
        db.session.add_all([service, round_obj, check])
        db.session.commit()

        self.login("whiteuser")

        with patch("scoring_engine.web.views.api.admin.update_scoreboard_data") as mock_scoreboard:
            with patch("scoring_engine.web.views.api.admin.update_overview_data") as mock_overview:
                self.client.post(
                    "/api/admin/update_check", data={"pk": check.id, "name": "check_value", "value": "2"}
                )
                mock_scoreboard.assert_called_once()
                mock_overview.assert_called_once()

    def test_admin_update_check_invalid_value(self):
        """Test that invalid check values are handled"""
        service = Service(name="Test", check_name="ICMP IPv4 Check", host="1.2.3.4", team=self.blue_team)
        round_obj = Round(number=1)
        check = Check(service=service, round=round_obj, result=True, output="test")
        db.session.add_all([service, round_obj, check])
        db.session.commit()

        self.login("whiteuser")

        # Invalid value (not 1 or 2)
        with patch("scoring_engine.web.views.api.admin.update_scoreboard_data"):
            with patch("scoring_engine.web.views.api.admin.update_overview_data"):
                self.client.post(
                    "/api/admin/update_check", data={"pk": check.id, "name": "check_value", "value": "3"}
                )

        # Should not crash, just not update
        db.session.refresh(check)
        assert check.result is True  # Unchanged

    # SQL Injection Tests
    def test_admin_update_environment_sql_injection_prevention(self):
        """SECURITY: Test SQL injection prevention in environment updates"""
        service = Service(name="Test", check_name="ICMP IPv4 Check", host="1.2.3.4", team=self.blue_team)
        env = Environment(service=service, matching_content="test")
        db.session.add_all([service, env])
        db.session.commit()

        self.login("whiteuser")

        sql_injections = [
            "'; DROP TABLE environment; --",
            "1' OR '1'='1",
            "' UNION SELECT password FROM users--",
        ]

        for injection in sql_injections:
            resp = self.client.post(
                "/api/admin/update_environment_info",
                data={"pk": env.id, "name": "matching_content", "value": injection},
            )
            assert resp.status_code == 200
            db.session.refresh(env)
            assert env.matching_content == html.escape(injection)

    def test_admin_update_property_sql_injection_prevention(self):
        """SECURITY: Test SQL injection prevention in property updates"""
        service = Service(name="Test", check_name="ICMP IPv4 Check", host="1.2.3.4", team=self.blue_team)
        env = Environment(service=service, matching_content="test")
        prop = Property(name="key", value="value", environment=env)
        db.session.add_all([service, env, prop])
        db.session.commit()

        self.login("whiteuser")

        sql_injection = "'; DROP TABLE property; --"
        resp = self.client.post(
            "/api/admin/update_property", data={"pk": prop.id, "name": "property_value", "value": sql_injection}
        )
        assert resp.status_code == 200
        db.session.refresh(prop)
        assert prop.value == html.escape(sql_injection)

    def test_admin_update_environment_rejects_invalid_regex(self):
        """Test that invalid regex patterns are rejected when updating matching_content"""
        service = Service(name="Test", check_name="ICMP IPv4 Check", host="1.2.3.4", team=self.blue_team)
        env = Environment(service=service, matching_content="old_value")
        db.session.add_all([service, env])
        db.session.commit()

        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/update_environment_info", data={"pk": env.id, "name": "matching_content", "value": "foo(bar"}
        )

        assert resp.status_code == 400
        assert "Invalid regex pattern" in resp.json["error"]

        db.session.refresh(env)
        assert env.matching_content == "old_value"

    def test_admin_update_environment_accepts_valid_regex(self):
        """Test that valid regex patterns are accepted when updating matching_content"""
        service = Service(name="Test", check_name="ICMP IPv4 Check", host="1.2.3.4", team=self.blue_team)
        env = Environment(service=service, matching_content="old_value")
        db.session.add_all([service, env])
        db.session.commit()

        self.login("whiteuser")
        resp = self.client.post(
            "/api/admin/update_environment_info", data={"pk": env.id, "name": "matching_content", "value": "^SUCCESS"}
        )

        assert resp.status_code == 200
        assert resp.json["status"] == "Updated Environment Information"

        db.session.refresh(env)
        assert env.matching_content == "^SUCCESS"

    def test_admin_nonexistent_environment(self):
        """Test updating nonexistent environment returns error"""
        self.login("whiteuser")

        resp = self.client.post(
            "/api/admin/update_environment_info", data={"pk": 99999, "name": "matching_content", "value": "test"}
        )
        assert "error" in resp.json or resp.json.get("status") != "Updated Environment Information"

    def test_admin_nonexistent_property(self):
        """Test updating nonexistent property returns error"""
        self.login("whiteuser")

        resp = self.client.post(
            "/api/admin/update_property", data={"pk": 99999, "name": "property_name", "value": "test"}
        )
        assert "error" in resp.json or resp.json.get("status") != "Updated Property Information"

    def test_admin_nonexistent_check(self):
        """Test updating nonexistent check returns error"""
        self.login("whiteuser")

        resp = self.client.post("/api/admin/update_check", data={"pk": 99999, "name": "check_value", "value": "1"})
        assert "error" in resp.json or resp.json.get("status") != "Updated Check Information"

    # Engine Toggle Tests
    def test_toggle_engine_requires_white_team(self):
        """Test that only white team can toggle engine"""
        self.login("blueuser")
        resp = self.client.post("/api/admin/toggle_engine")
        assert resp.status_code == 403
        assert resp.json["status"] == "Unauthorized"

    def test_toggle_engine_pauses_running_engine(self):
        """Test toggling engine from running to paused"""
        self.login("whiteuser")

        resp = self.client.get("/api/admin/get_engine_paused")
        assert resp.status_code == 200
        assert resp.json["paused"] is False

        resp = self.client.post("/api/admin/toggle_engine")
        assert resp.status_code == 200
        assert resp.json["status"] == "Success"

        resp = self.client.get("/api/admin/get_engine_paused")
        assert resp.status_code == 200
        assert resp.json["paused"] is True

    def test_toggle_engine_resumes_paused_engine(self):
        """Test toggling engine from paused back to running"""
        self.login("whiteuser")

        self.client.post("/api/admin/toggle_engine")
        resp = self.client.get("/api/admin/get_engine_paused")
        assert resp.json["paused"] is True

        resp = self.client.post("/api/admin/toggle_engine")
        assert resp.status_code == 200

        resp = self.client.get("/api/admin/get_engine_paused")
        assert resp.json["paused"] is False

    def test_toggle_engine_persists_to_database(self):
        """Test that toggle actually persists the value to the database"""
        self.login("whiteuser")

        setting = Setting.get_setting("engine_paused")
        assert setting.value is False

        resp = self.client.post("/api/admin/toggle_engine")
        assert resp.status_code == 200

        setting = db.session.query(Setting).filter(Setting.name == "engine_paused").order_by(Setting.id.desc()).first()
        assert setting.value is True

    def test_toggle_engine_clears_cache(self):
        """Test that toggle clears the Redis cache for engine_paused"""
        from scoring_engine.models.setting import CACHE_PREFIX

        self.login("whiteuser")

        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        with patch("scoring_engine.models.setting._get_redis", return_value=mock_redis):
            self.client.post("/api/admin/toggle_engine")

        mock_redis.delete.assert_called_with(CACHE_PREFIX + "engine_paused")

    def test_toggle_engine_with_stale_cache(self):
        """Test that toggle reads from DB when Redis cache is stale"""
        self.login("whiteuser")

        setting = db.session.query(Setting).filter(Setting.name == "engine_paused").first()
        setting.value = True
        db.session.commit()

        resp = self.client.post("/api/admin/toggle_engine")
        assert resp.status_code == 200

        setting = db.session.query(Setting).filter(Setting.name == "engine_paused").order_by(Setting.id.desc()).first()
        assert setting.value is False

    def test_get_engine_paused_requires_white_team(self):
        """Test that only white team can get engine status"""
        self.login("blueuser")
        resp = self.client.get("/api/admin/get_engine_paused")
        assert resp.status_code == 403

    def test_get_engine_paused_returns_boolean(self):
        """Test that paused status is returned as a JSON boolean, not string"""
        self.login("whiteuser")
        resp = self.client.get("/api/admin/get_engine_paused")
        assert resp.status_code == 200
        assert resp.json["paused"] is False
        assert isinstance(resp.json["paused"], bool)

    def test_get_engine_paused_reads_from_db(self):
        """Test that get_engine_paused returns the current DB value"""
        self.login("whiteuser")

        setting = db.session.query(Setting).filter(Setting.name == "engine_paused").first()
        setting.value = True
        db.session.commit()

        resp = self.client.get("/api/admin/get_engine_paused")
        assert resp.json["paused"] is True
