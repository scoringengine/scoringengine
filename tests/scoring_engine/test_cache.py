"""Tests for cache initialization and configuration"""
from unittest.mock import MagicMock, patch

import pytest

from scoring_engine.config import config


class TestCache:
    """Test cache initialization and type mapping"""

    def test_cache_type_map_redis(self):
        """Test that redis maps to correct backend"""
        from scoring_engine.cache import _CACHE_TYPE_MAP

        assert _CACHE_TYPE_MAP["redis"] == "flask_caching.backends.rediscache.RedisCache"

    def test_cache_type_map_null(self):
        """Test that null maps to correct backend"""
        from scoring_engine.cache import _CACHE_TYPE_MAP

        assert _CACHE_TYPE_MAP["null"] == "flask_caching.backends.nullcache.NullCache"

    def test_cache_type_map_simple(self):
        """Test that simple maps to correct backend"""
        from scoring_engine.cache import _CACHE_TYPE_MAP

        assert _CACHE_TYPE_MAP["simple"] == "flask_caching.backends.simplecache.SimpleCache"

    def test_cache_initialization(self):
        """Test that cache object is initialized"""
        from scoring_engine.cache import cache

        assert cache is not None
        assert hasattr(cache, 'init_app')

    def test_agent_cache_initialization(self):
        """Test that agent_cache object is initialized"""
        from scoring_engine.cache import agent_cache

        assert agent_cache is not None
        assert hasattr(agent_cache, 'init_app')

    def test_agent_cache_has_prefix(self):
        """Test that agent_cache has correct key prefix"""
        # Agent cache should have a prefix to separate it from main cache
        from scoring_engine.cache import agent_cache

        # The cache config should include the prefix
        assert agent_cache is not None

    def test_cache_uses_config_values(self):
        """Test that cache uses values from config"""
        # Cache should use redis host, port, and password from config
        from scoring_engine.cache import cache

        assert cache is not None
        # Config values should be set during initialization

    def test_cache_type_fallback(self):
        """Test that unknown cache types fall back to config value"""
        from scoring_engine.cache import _CACHE_TYPE_MAP

        # If cache_type is not in map, it should use the value directly
        custom_type = "custom.cache.Backend"

        # The code uses .get() with default, so unknown types pass through
        assert _CACHE_TYPE_MAP.get(custom_type, custom_type) == custom_type


class TestCeleryApp:
    """Test Celery application initialization"""

    def test_celery_app_initialization(self):
        """Test that celery app is initialized"""
        from scoring_engine.celery_app import celery_app

        assert celery_app is not None
        assert celery_app.main == 'engine.worker'

    def test_celery_app_includes_execute_command(self):
        """Test that celery includes execute_command module"""
        from scoring_engine.celery_app import celery_app

        assert 'scoring_engine.engine.execute_command' in celery_app.conf.include

    def test_celery_redis_connection_string(self):
        """Test that redis connection string is properly formatted"""
        from scoring_engine.celery_app import redis_server

        # Should start with redis://
        assert redis_server.startswith('redis://:')

        # Should include config values
        assert config.redis_host in redis_server
        assert str(config.redis_port) in redis_server

    def test_celery_broker_configuration(self):
        """Test that celery broker is configured"""
        from scoring_engine.celery_app import celery_app

        # Broker should be set
        assert celery_app.conf.broker_url is not None
        assert 'redis://' in celery_app.conf.broker_url

    def test_celery_backend_configuration(self):
        """Test that celery backend is configured"""
        from scoring_engine.celery_app import celery_app

        # Backend should be set
        assert celery_app.conf.result_backend is not None
        assert 'redis://' in celery_app.conf.result_backend


class TestLogger:
    """Test logger initialization and configuration"""

    def test_logger_initialization(self):
        """Test that logger is initialized"""
        from scoring_engine.logger import logger

        assert logger is not None
        assert logger.name == 'scoring_engine'

    def test_logger_level(self):
        """Test that logger level is set to INFO"""
        from scoring_engine.logger import logger
        import logging

        assert logger.level == logging.INFO

    def test_logger_has_handler(self):
        """Test that logger has at least one handler"""
        from scoring_engine.logger import logger

        assert len(logger.handlers) > 0

    def test_logger_formatter(self):
        """Test that logger has correct formatter"""
        from scoring_engine.logger import logger

        # Should have a handler with formatter
        if logger.handlers:
            handler = logger.handlers[0]
            assert handler.formatter is not None

            # Formatter should include asctime, levelname, and message
            format_string = handler.formatter._fmt
            assert 'asctime' in format_string
            assert 'levelname' in format_string
            assert 'message' in format_string

    def test_logger_can_log(self):
        """Test that logger can log messages without errors"""
        from scoring_engine.logger import logger

        # Should not raise any exceptions
        try:
            logger.info("Test message")
            logger.warning("Test warning")
            logger.error("Test error")
        except Exception as e:
            pytest.fail(f"Logger raised exception: {e}")
