import os
import sys
import re

from scoring_engine.version import version

from tests.scoring_engine.unit_test import UnitTest


class MockConfigTrueDebug():
    @property
    def debug(self):
        return True


class MockConfigFalseDebug():
    @property
    def debug(self):
        return False


class TestVersion(UnitTest):

    def setup(self):
        super(TestVersion, self).setup()
        if 'SCORINGENGINE_VERSION' in os.environ:
            del os.environ['SCORINGENGINE_VERSION']
        self.toggle_debug(False)

    def toggle_debug(self, result):
        if 'scoring_engine.config' in sys.modules:
            del sys.modules['scoring_engine.config']
        import scoring_engine.config

        if result:
            scoring_engine.config_loader.ConfigLoader = MockConfigTrueDebug
        else:
            scoring_engine.config_loader.ConfigLoader = MockConfigFalseDebug

        if 'scoring_engine.config' in sys.modules:
            del sys.modules['scoring_engine.config']
        from scoring_engine.config import config
        assert getattr(config, 'debug', None) is not None

    def test_normal_version(self):
        # Verify it's a X.X.X
        assert re.search(r'([\d.]+)', version).group(1) == version

    def test_environment_var_version(self):
        os.environ['SCORINGENGINE_VERSION'] = 'testver'
        if 'scoring_engine.version' in sys.modules:
            del sys.modules["scoring_engine.version"]
        from scoring_engine.version import version
        assert version == 'testver'

    def test_debug_version(self):
        self.toggle_debug(True)
        if 'scoring_engine.version' in sys.modules:
            del sys.modules["scoring_engine.version"]
        from scoring_engine.version import version
        # Verify it's a X.X.X-dev
        assert re.search(r'([\d.]+-dev)', version).group(1) == version

    def test_debug_env_version(self):
        self.toggle_debug(True)
        os.environ['SCORINGENGINE_VERSION'] = 'abcdefg'
        if 'scoring_engine.version' in sys.modules:
            del sys.modules["scoring_engine.version"]
        from scoring_engine.version import version
        assert 'abcdefg-dev' == version
