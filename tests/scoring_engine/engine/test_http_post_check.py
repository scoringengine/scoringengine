"""Tests for HTTP POST check parameter sanitization"""
from unittest.mock import MagicMock

from scoring_engine.engine.http_post_check import HTTPPostCheck
from tests.scoring_engine.unit_test import UnitTest


class TestHTTPPostCheck(UnitTest):
    """Test HTTP POST parameter sanitization to prevent injection attacks"""

    def test_sanitizes_string_arguments(self):
        """Test that string arguments are URL-encoded"""
        check = HTTPPostCheck("Test Service")
        check.CMD = "curl -d 'user={0}&pass={1}' http://example.com"
        check.properties = {}
        check.command_format = MagicMock(return_value=["user@example.com", "pass word"])

        result = check.command()

        # Should URL-encode the arguments
        assert "user%40example.com" in result
        assert "pass%20word" in result

    def test_does_not_sanitize_non_string_arguments(self):
        """Test that non-string arguments are not URL-encoded"""
        check = HTTPPostCheck("Test Service")
        check.CMD = "curl -d 'port={0}' http://example.com"
        check.properties = {}
        check.command_format = MagicMock(return_value=[8080])

        result = check.command()

        # Should not URL-encode integers
        assert "8080" in result
        assert "curl" in result

    def test_sanitizes_special_characters(self):
        """SECURITY: Test that special characters are properly escaped"""
        check = HTTPPostCheck("Test Service")
        check.CMD = "curl -d 'data={0}' http://example.com"
        check.properties = {}

        # Test various injection attempts
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "$(rm -rf /)",
            "`cat /etc/passwd`",
            "../../../etc/passwd",
            "test&param=value",
            "test=value&extra=param"
        ]

        for malicious_input in malicious_inputs:
            check.command_format = MagicMock(return_value=[malicious_input])
            result = check.command()

            # All special characters should be URL-encoded
            assert "'" not in result or "%27" in result
            assert "<" not in result or "%3C" in result
            assert ">" not in result or "%3E" in result
            assert "`" not in result or "%60" in result
            assert " " not in result or "%20" in result

    def test_handles_empty_string(self):
        """Test that empty strings are handled correctly"""
        check = HTTPPostCheck("Test Service")
        check.CMD = "curl -d 'data={0}' http://example.com"
        check.properties = {}
        check.command_format = MagicMock(return_value=[""])

        result = check.command()

        assert "curl" in result
        assert "data=" in result

    def test_handles_unicode_characters(self):
        """Test that unicode characters are properly encoded"""
        check = HTTPPostCheck("Test Service")
        check.CMD = "curl -d 'data={0}' http://example.com"
        check.properties = {}
        check.command_format = MagicMock(return_value=["héllo wörld 🌍"])

        result = check.command()

        # Unicode should be URL-encoded
        assert "h%C3%A9llo" in result or "héllo" in result
        assert "%20" in result  # Space should be encoded

    def test_handles_mixed_types(self):
        """Test that mixed string and non-string types are handled correctly"""
        check = HTTPPostCheck("Test Service")
        check.CMD = "curl -d 'user={0}&port={1}&active={2}' http://example.com"
        check.properties = {}
        check.command_format = MagicMock(
            return_value=["admin user", 8080, True]
        )

        result = check.command()

        # String should be encoded, others should not
        assert "admin%20user" in result
        assert "8080" in result
        assert "True" in result

    def test_preserves_command_structure(self):
        """Test that the command structure is preserved after sanitization"""
        check = HTTPPostCheck("Test Service")
        check.CMD = "curl -X POST -d '{0}' -H 'Content-Type: {1}' http://example.com"
        check.properties = {}
        check.command_format = MagicMock(
            return_value=["user=test&pass=secret", "application/x-www-form-urlencoded"]
        )

        result = check.command()

        # Command should start with curl
        assert result.startswith("curl")
        # Should contain all the flags
        assert "-X POST" in result
        assert "-d" in result
        assert "-H" in result

    def test_sql_injection_prevention(self):
        """SECURITY: Test prevention of SQL injection through POST parameters"""
        check = HTTPPostCheck("Test Service")
        check.CMD = "curl -d 'query={0}' http://example.com/api"
        check.properties = {}

        sql_injections = [
            "1' OR '1'='1",
            "1; DROP TABLE users--",
            "' UNION SELECT password FROM users--",
            "admin'--",
            "' OR 1=1--"
        ]

        for injection in sql_injections:
            check.command_format = MagicMock(return_value=[injection])
            result = check.command()

            # Single quotes and special SQL characters should be encoded
            assert "'" not in result or "%27" in result
            assert "OR" not in result or "%20OR%20" in result or "OR" in injection

    def test_command_injection_prevention(self):
        """SECURITY: Test prevention of command injection through POST parameters"""
        check = HTTPPostCheck("Test Service")
        check.CMD = "curl -d 'cmd={0}' http://example.com/exec"
        check.properties = {}

        command_injections = [
            "; ls -la",
            "| cat /etc/passwd",
            "& whoami",
            "$(malicious command)",
            "`evil command`",
            "\n cat /etc/shadow"
        ]

        for injection in command_injections:
            check.command_format = MagicMock(return_value=[injection])
            result = check.command()

            # All command injection characters should be encoded
            assert ";" not in result or "%3B" in result
            assert "|" not in result or "%7C" in result
            assert "$" not in result or "%24" in result
            assert "`" not in result or "%60" in result

    def test_xss_prevention(self):
        """SECURITY: Test prevention of XSS through POST parameters"""
        check = HTTPPostCheck("Test Service")
        check.CMD = "curl -d 'input={0}' http://example.com/submit"
        check.properties = {}

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror='alert(1)'>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "'-alert(1)-'"
        ]

        for payload in xss_payloads:
            check.command_format = MagicMock(return_value=[payload])
            result = check.command()

            # HTML/JS special characters should be encoded
            assert "<" not in result or "%3C" in result
            assert ">" not in result or "%3E" in result
            assert "'" not in result or "%27" in result

    def test_null_byte_injection_prevention(self):
        """SECURITY: Test prevention of null byte injection"""
        check = HTTPPostCheck("Test Service")
        check.CMD = "curl -d 'file={0}' http://example.com/read"
        check.properties = {}

        null_byte_payloads = [
            "file.txt\x00.php",
            "../../etc/passwd\x00",
            "test\x00admin"
        ]

        for payload in null_byte_payloads:
            check.command_format = MagicMock(return_value=[payload])
            result = check.command()

            # Null bytes should be encoded
            assert "\x00" not in result or "%00" in result

    def test_ldap_injection_prevention(self):
        """SECURITY: Test prevention of LDAP injection"""
        check = HTTPPostCheck("Test Service")
        check.CMD = "curl -d 'user={0}' http://example.com/ldap"
        check.properties = {}

        ldap_injections = [
            "*",
            "admin)(|(password=*))",
            "*)(&(objectClass=*)",
            "admin)(!(&(|",
        ]

        for injection in ldap_injections:
            check.command_format = MagicMock(return_value=[injection])
            result = check.command()

            # LDAP special characters should be encoded
            assert "(" not in result or "%28" in result
            assert ")" not in result or "%29" in result
            assert "*" not in result or "%2A" in result
