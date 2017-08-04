from scoring_engine.models.setting import Setting

from tests.scoring_engine.unit_test import UnitTest


class TestSetting(UnitTest):

    def test_init_setting(self):
        setting = Setting(name='test_setting', value='test value example')
        assert setting.id is None
        assert setting.name == 'test_setting'
        assert setting.value == 'test value example'
        self.db.save(setting)
        assert setting.id is not None

    def test_get_setting(self):
        setting_old = Setting(name='test_setting', value='test value example')
        self.db.save(setting_old)
        setting_new = Setting(name='test_setting', value='updated example')
        self.db.save(setting_new)
        assert Setting.get_setting('test_setting') == 'updated example'
