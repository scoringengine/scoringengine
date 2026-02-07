from scoring_engine.models.setting import Setting

from tests.scoring_engine.unit_test import UnitTest
from time import sleep


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

    def test_get_setting_caching(self):
        # Clear cache before test
        Setting.clear_cache()

        # Create a setting
        setting = Setting(name='cached_setting', value='initial_value')
        self.session.add(setting)
        self.session.commit()

        # First call should query database and cache the result
        result1 = Setting.get_setting('cached_setting')
        assert result1.value == 'initial_value'
        assert 'cached_setting' in Setting._cache

        # Second call should return cached value with same data
        result2 = Setting.get_setting('cached_setting')
        assert result2.value == 'initial_value'
        assert result1.id == result2.id  # Same setting from cache

    def test_get_setting_cache_expiration(self):
        # Clear cache before test
        Setting.clear_cache()

        # Set a very short TTL for testing
        original_ttl = Setting._cache_ttl
        Setting._cache_ttl = 1  # 1 second TTL

        # Create a setting
        setting = Setting(name='expiring_setting', value='first_value')
        self.session.add(setting)
        self.session.commit()

        # First call caches the setting
        result1 = Setting.get_setting('expiring_setting')
        assert result1.value == 'first_value'

        # Update the setting in database
        new_setting = Setting(name='expiring_setting', value='second_value')
        self.session.add(new_setting)
        self.session.commit()

        # Immediate call should still return cached value
        result2 = Setting.get_setting('expiring_setting')
        assert result2.value == 'first_value'

        # Wait for cache to expire
        sleep(1.5)

        # After expiration, should get updated value from database
        result3 = Setting.get_setting('expiring_setting')
        assert result3.value == 'second_value'

        # Restore original TTL
        Setting._cache_ttl = original_ttl

    def test_clear_cache_all(self):
        # Create and cache multiple settings
        setting1 = Setting(name='setting1', value='value1')
        setting2 = Setting(name='setting2', value='value2')
        self.session.add(setting1)
        self.session.add(setting2)
        self.session.commit()

        Setting.get_setting('setting1')
        Setting.get_setting('setting2')

        assert len(Setting._cache) >= 2

        # Clear entire cache
        Setting.clear_cache()
        assert len(Setting._cache) == 0

    def test_clear_cache_specific(self):
        # Clear cache before test
        Setting.clear_cache()

        # Create and cache multiple settings
        setting1 = Setting(name='setting_a', value='value_a')
        setting2 = Setting(name='setting_b', value='value_b')
        self.session.add(setting1)
        self.session.add(setting2)
        self.session.commit()

        Setting.get_setting('setting_a')
        Setting.get_setting('setting_b')

        assert 'setting_a' in Setting._cache
        assert 'setting_b' in Setting._cache

        # Clear only one setting from cache
        Setting.clear_cache('setting_a')
        assert 'setting_a' not in Setting._cache
        assert 'setting_b' in Setting._cache

    def test_get_setting_use_cache_false(self):
        """Test that use_cache=False bypasses in-memory cache and reads from DB"""
        # Clear cache before test
        Setting.clear_cache()

        # Create a setting and cache it
        setting = Setting(name='bypass_test', value='original')
        self.session.add(setting)
        self.session.commit()

        # Prime the cache
        result = Setting.get_setting('bypass_test')
        assert result.value == 'original'
        assert 'bypass_test' in Setting._cache

        # Update the DB directly (simulates another worker's write)
        from scoring_engine.db import db
        new_setting = Setting(name='bypass_test', value='updated')
        db.session.add(new_setting)
        db.session.commit()

        # With cache: should still return old value
        cached_result = Setting.get_setting('bypass_test')
        assert cached_result.value == 'original'

        # Without cache: should return the new DB value
        fresh_result = Setting.get_setting('bypass_test', use_cache=False)
        assert fresh_result.value == 'updated'

    def test_get_setting_use_cache_false_still_updates_cache(self):
        """Test that use_cache=False still stores the fresh result in cache"""
        Setting.clear_cache()

        setting = Setting(name='cache_update_test', value='value1')
        self.session.add(setting)
        self.session.commit()

        # Bypass cache on read - should still populate the cache
        Setting.get_setting('cache_update_test', use_cache=False)
        assert 'cache_update_test' in Setting._cache

    def test_setting_toggle_persists(self):
        """Test that toggling a boolean setting persists correctly to DB"""
        Setting.clear_cache()

        # Read the engine_paused setting (created by unit_test setup)
        setting = Setting.get_setting('engine_paused', use_cache=False)
        assert setting.value is False

        # Toggle it
        setting.value = not setting.value
        self.session.add(setting)
        self.session.commit()
        Setting.clear_cache('engine_paused')

        # Read fresh from DB - should be True
        setting = Setting.get_setting('engine_paused', use_cache=False)
        assert setting.value is True

        # Toggle back
        setting.value = not setting.value
        self.session.add(setting)
        self.session.commit()
        Setting.clear_cache('engine_paused')

        # Read fresh from DB - should be False again
        setting = Setting.get_setting('engine_paused', use_cache=False)
        assert setting.value is False
