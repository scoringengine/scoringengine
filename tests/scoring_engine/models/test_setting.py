import json
from unittest.mock import MagicMock, patch

from scoring_engine.models.setting import Setting, CACHE_PREFIX, CACHE_TTL

from tests.scoring_engine.unit_test import UnitTest


class TestSetting(UnitTest):

    def test_init_setting(self):
        setting = Setting(name='test_setting', value='test value example')
        assert setting.id is None
        assert setting.name == 'test_setting'
        assert setting.value == 'test value example'
        assert setting._value_type == 'String'
        self.session.add(setting)
        self.session.commit()
        assert setting.id is not None

    def test_get_setting(self):
        setting_old = Setting(name='test_setting', value='test value example')
        self.session.add(setting_old)
        setting_new = Setting(name='test_setting', value='updated example')
        self.session.add(setting_new)
        self.session.commit()
        assert Setting.get_setting('test_setting').value == 'updated example'

    def test_boolean_value(self):
        setting = Setting(name='test_setting', value=True)
        assert setting.name == 'test_setting'
        assert setting.value is True
        self.session.add(setting)
        self.session.commit()
        assert setting.value is True

    def test_boolean_value_negative(self):
        setting = Setting(name='test_setting', value=False)
        assert setting.name == 'test_setting'
        assert setting.value is False
        self.session.add(setting)
        self.session.commit()
        assert setting.value is False

    def test_boolean_value_advanced(self):
        setting = Setting(name='test_setting', value=True)
        assert setting.name == 'test_setting'
        assert setting.value is True
        self.session.add(setting)
        self.session.commit()
        setting.value = 'somevalue'
        assert setting.value == 'somevalue'
        self.session.add(setting)
        self.session.commit()

    def test_get_setting_no_redis_falls_back_to_db(self):
        """Without Redis, get_setting always queries the database."""
        setting = Setting(name='db_only', value='direct')
        self.session.add(setting)
        self.session.commit()

        result = Setting.get_setting('db_only')
        assert result.value == 'direct'

    def test_get_setting_redis_cache_hit(self):
        """When Redis has a cached entry, get_setting returns it without querying DB."""
        setting = Setting(name='cached_bool', value=True)
        self.session.add(setting)
        self.session.commit()

        cached_payload = json.dumps({
            "id": setting.id,
            "value_text": "True",
            "value_type": "Boolean",
        })

        mock_redis = MagicMock()
        mock_redis.get.return_value = cached_payload

        with patch("scoring_engine.models.setting._get_redis", return_value=mock_redis):
            result = Setting.get_setting('cached_bool')

        assert result.value is True
        mock_redis.get.assert_called_once_with(CACHE_PREFIX + "cached_bool")

    def test_get_setting_redis_cache_miss_populates_cache(self):
        """On cache miss, get_setting queries DB and writes to Redis."""
        setting = Setting(name='miss_test', value='hello')
        self.session.add(setting)
        self.session.commit()

        mock_redis = MagicMock()
        mock_redis.get.return_value = None  # cache miss

        with patch("scoring_engine.models.setting._get_redis", return_value=mock_redis):
            result = Setting.get_setting('miss_test')

        assert result.value == 'hello'
        # Should have written to Redis
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == CACHE_PREFIX + "miss_test"
        assert call_args[1]["ex"] == CACHE_TTL
        # Verify the payload
        payload = json.loads(call_args[0][1])
        assert payload["value_text"] == "hello"
        assert payload["value_type"] == "String"

    def test_clear_cache_specific_key(self):
        """clear_cache(name) deletes that specific Redis key."""
        mock_redis = MagicMock()
        with patch("scoring_engine.models.setting._get_redis", return_value=mock_redis):
            Setting.clear_cache("engine_paused")

        mock_redis.delete.assert_called_once_with(CACHE_PREFIX + "engine_paused")

    def test_clear_cache_all(self):
        """clear_cache() deletes all setting keys from Redis."""
        mock_redis = MagicMock()
        mock_redis.keys.return_value = [
            CACHE_PREFIX + "a",
            CACHE_PREFIX + "b",
        ]
        with patch("scoring_engine.models.setting._get_redis", return_value=mock_redis):
            Setting.clear_cache()

        mock_redis.keys.assert_called_once_with(CACHE_PREFIX + "*")
        mock_redis.delete.assert_called_once_with(
            CACHE_PREFIX + "a",
            CACHE_PREFIX + "b",
        )

    def test_clear_cache_noop_without_redis(self):
        """clear_cache does nothing when Redis is unavailable."""
        # Should not raise
        Setting.clear_cache()
        Setting.clear_cache("engine_paused")

    def test_setting_toggle_persists(self):
        """Test that toggling a boolean setting persists correctly to DB."""
        # Read the engine_paused setting (created by unit_test setup)
        setting = Setting.get_setting('engine_paused')
        assert setting.value is False

        # Toggle it
        setting.value = not setting.value
        self.session.add(setting)
        self.session.commit()

        # Read fresh from DB - should be True
        setting = Setting.get_setting('engine_paused')
        assert setting.value is True

        # Toggle back
        setting.value = not setting.value
        self.session.add(setting)
        self.session.commit()

        # Read fresh from DB - should be False again
        setting = Setting.get_setting('engine_paused')
        assert setting.value is False

    def test_toggle_and_clear_cache_updates_all_workers(self):
        """Simulates the multi-worker scenario: toggle + clear_cache ensures
        the next read (from any worker) sees the updated value."""
        mock_redis = MagicMock()
        # First call: cache miss, second call: also miss (cache was cleared)
        mock_redis.get.return_value = None

        with patch("scoring_engine.models.setting._get_redis", return_value=mock_redis):
            # Read current value
            setting = Setting.get_setting('engine_paused')
            assert setting.value is False

            # Toggle
            setting.value = not setting.value
            self.session.add(setting)
            self.session.commit()

            # Clear cache (this is what makes it visible to other workers)
            Setting.clear_cache('engine_paused')
            mock_redis.delete.assert_called_with(CACHE_PREFIX + "engine_paused")

            # Next read should hit DB and get the new value
            setting = Setting.get_setting('engine_paused')
            assert setting.value is True
