import os
import sys
import re

from scoring_engine.version import version

from tests.scoring_engine.unit_test import UnitTest


class MockConfigLoader():
    def __init__(self):
        self.mock_keyname = True

    @property
    def debug(self):
        return True


class TestVersion(UnitTest):

    def setup(self):
        super(TestVersion, self).setup()
        if 'SCORINGENGINE_VERSION' in os.environ:
            del os.environ['SCORINGENGINE_VERSION']

    def enable_debug(self):
        if 'scoring_engine.config_loader' in sys.modules:
            del sys.modules['scoring_engine.config_loader']
        import scoring_engine.config_loader

        scoring_engine.config_loader.ConfigLoader = MockConfigLoader

        if 'scoring_engine.config' in sys.modules:
            del sys.modules['scoring_engine.config']
        from scoring_engine.config import config

    def test_normal_version(self):
        # Verify it's a X.X.X
        assert re.search(r'([\d.]+)', version).group(1) == version

    def test_environment_var_version(self):
        os.environ['SCORINGENGINE_VERSION'] = 'testver'
        del sys.modules["scoring_engine.version"]
        from scoring_engine.version import version
        assert version == 'testver'

    def test_debug_version(self):
        self.enable_debug()
        del sys.modules["scoring_engine.version"]
        from scoring_engine.version import version
        # Verify it's a X.X.X-dev
        assert re.search(r'([\d.]+-dev)', version).group(1) == version

    def test_debug_env_version(self):
        self.enable_debug()
        os.environ['SCORINGENGINE_VERSION'] = 'abcdefg'
        del sys.modules["scoring_engine.version"]
        from scoring_engine.version import version
        assert 'abcdefg-dev' == version
