import importlib
import sys


class MockConfigLoader:
    def __init__(self):
        self.mock_keyname = True


class TestConfig(object):

    def test_config_variable(self, monkeypatch):
        # monkeypatch restores ConfigLoader and the sys.modules entries after
        # the test, so the mocked config can't leak into later tests.
        # import_module reads sys.modules directly; other tests may have
        # re-imported config_loader, so the package attribute can be stale.
        config_loader = importlib.import_module("scoring_engine.config_loader")
        monkeypatch.setattr(config_loader, "ConfigLoader", MockConfigLoader)
        monkeypatch.delitem(sys.modules, "scoring_engine.config", raising=False)
        from scoring_engine.config import config

        assert config.mock_keyname is True
