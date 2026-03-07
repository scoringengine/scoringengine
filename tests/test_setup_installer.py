import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import setup_installer
from setup_installer import (
    _set_ini_value,
    get_config_noninteractive,
    redact_config_for_print,
    write_compose_override,
    write_env,
)


class TestSetIniValue(unittest.TestCase):
    def test_replaces_existing_key(self):
        text = "[OPTIONS]\ndb_uri = old_value\n"
        result = _set_ini_value(text, "db_uri", "new_value")
        assert "db_uri = new_value" in result
        assert "old_value" not in result

    def test_replaces_commented_key(self):
        text = "[OPTIONS]\n# db_uri = example\n"
        result = _set_ini_value(text, "db_uri", "new_value")
        assert "db_uri = new_value" in result
        assert "#" not in result

    def test_inserts_after_options_section(self):
        text = "[OPTIONS]\n"
        result = _set_ini_value(text, "new_key", "val")
        lines = result.splitlines()
        options_idx = lines.index("[OPTIONS]")
        assert lines[options_idx + 1] == "new_key = val"

    def test_appends_when_no_options_section(self):
        text = "some = config\n"
        result = _set_ini_value(text, "new_key", "val")
        assert "new_key = val" in result


class TestRedactConfigForPrint(unittest.TestCase):
    def _make_config(self):
        return {
            "engine": {"agent_psk": "secret"},
            "database": {"password": "dbpass", "uri": "mysql://user:dbpass@host/db"},
            "redis": {"redis_password": "redispass"},
        }

    def test_redacts_db_password(self):
        config = self._make_config()
        result = redact_config_for_print(config)
        assert result["database"]["password"] == "********"

    def test_redacts_db_uri(self):
        config = self._make_config()
        result = redact_config_for_print(config)
        assert result["database"]["uri"] == "<redacted>"

    def test_redacts_redis_password(self):
        config = self._make_config()
        result = redact_config_for_print(config)
        assert result["redis"]["redis_password"] == "********"

    def test_redacts_agent_psk(self):
        config = self._make_config()
        result = redact_config_for_print(config)
        assert result["engine"]["agent_psk"] == "********"

    def test_does_not_mutate_original(self):
        config = self._make_config()
        redact_config_for_print(config)
        assert config["database"]["password"] == "dbpass"
        assert config["database"]["uri"] == "mysql://user:dbpass@host/db"

    def test_empty_redis_password_not_redacted(self):
        config = self._make_config()
        config["redis"]["redis_password"] = ""
        result = redact_config_for_print(config)
        assert result["redis"]["redis_password"] == ""


class TestWriteComposeOverride(unittest.TestCase):
    def test_writes_correct_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(setup_installer, "CONFIG_DIR", Path(tmpdir)):
                write_compose_override()
                out = (Path(tmpdir) / "docker-compose.override.yml").read_text()
        assert "bootstrap:" in out
        assert "engine:" in out
        assert "worker:" in out
        assert "web:" in out
        assert "./docker/engine.conf.inc:/app/engine.conf:ro" in out


class TestWriteEnv(unittest.TestCase):
    def _config(self, redis_pw=""):
        return {
            "database": {"uri": "mysql://user:pass@host/db"},
            "redis": {"redis_host": "redis", "redis_port": "6379", "redis_password": redis_pw},
        }

    def test_writes_db_and_redis(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            with patch.object(setup_installer, "ENV_FILE", env_file):
                write_env(self._config())
            content = env_file.read_text()
        assert "DB_URI=mysql://user:pass@host/db" in content
        assert "REDIS_HOST=redis" in content
        assert "REDIS_PORT=6379" in content

    def test_redis_password_written_when_set(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            with patch.object(setup_installer, "ENV_FILE", env_file):
                write_env(self._config(redis_pw="secret"))
            content = env_file.read_text()
        assert "REDIS_PASSWORD=secret" in content

    def test_redis_password_omitted_when_blank(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            with patch.object(setup_installer, "ENV_FILE", env_file):
                write_env(self._config(redis_pw=""))
            content = env_file.read_text()
        assert "REDIS_PASSWORD" not in content


class TestGetConfigNoninteractive(unittest.TestCase):
    def test_defaults(self):
        env = {}
        with patch.dict(os.environ, env, clear=True):
            cfg = get_config_noninteractive()
        assert cfg["database"]["host"] == "mysql"
        assert cfg["database"]["port"] == "3306"
        assert cfg["redis"]["redis_host"] == "redis"
        assert cfg["competition"]["scoring_interval"] == "300"

    def test_env_var_overrides(self):
        env = {
            "SE_DB_HOST": "myhost",
            "SE_DB_PORT": "3307",
            "SE_DB_NAME": "mydb",
            "SE_DB_USER": "myuser",
            "SE_DB_PASSWORD": "mypass",
            "SE_REDIS_HOST": "myredis",
            "SE_REDIS_PORT": "6380",
            "SE_REDIS_PASSWORD": "redispass",
            "SE_SCORING_INTERVAL": "120",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = get_config_noninteractive()
        assert cfg["database"]["host"] == "myhost"
        assert cfg["database"]["port"] == "3307"
        assert cfg["redis"]["redis_host"] == "myredis"
        assert cfg["competition"]["scoring_interval"] == "120"

    def test_uri_encodes_special_chars_in_password(self):
        env = {
            "SE_DB_PASSWORD": "p@ss/w#rd",
            "SE_DB_HOST": "mysql",
            "SE_DB_PORT": "3306",
            "SE_DB_NAME": "scoring_engine",
            "SE_DB_USER": "se_user",
            "SE_REDIS_HOST": "redis",
            "SE_REDIS_PORT": "6379",
            "SE_REDIS_PASSWORD": "",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = get_config_noninteractive()
        assert "p%40ss%2Fw%23rd" in cfg["database"]["uri"]
        assert "p@ss/w#rd" not in cfg["database"]["uri"]
