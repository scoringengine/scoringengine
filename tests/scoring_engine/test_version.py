import importlib
import re
import sys

import pytest

from scoring_engine.version import version


class MockConfigTrueDebug:
    @property
    def debug(self):
        return True


class MockConfigFalseDebug:
    @property
    def debug(self):
        return False


class TestVersion:

    @pytest.fixture(autouse=True)
    def setup(self, db_session, monkeypatch):
        # monkeypatch restores everything below after each test, so the mocked
        # ConfigLoader/config and the re-imported version module can't leak
        # into later tests in the same worker.
        self.monkeypatch = monkeypatch
        monkeypatch.delenv("SCORINGENGINE_VERSION", raising=False)
        for module in ("scoring_engine.config", "scoring_engine.version"):
            if module in sys.modules:
                monkeypatch.setitem(sys.modules, module, sys.modules[module])
        self.toggle_debug(False)

    def toggle_debug(self, result):
        cl_mod = importlib.import_module("scoring_engine.config_loader")

        self.monkeypatch.setattr(cl_mod, "ConfigLoader", MockConfigTrueDebug if result else MockConfigFalseDebug)

        # Force scoring_engine.config to re-evaluate with the patched loader
        sys.modules.pop("scoring_engine.config", None)
        from scoring_engine.config import config

        assert getattr(config, "debug", None) is not None

    def test_normal_version(self):
        # Verify it's a X.X.X (possibly with +commit suffix)
        assert re.search(r"^[\d.]+", version).group(0) is not None

    def test_environment_var_commit_version(self):
        # When SCORINGENGINE_VERSION is a commit hash, it shows as version+commit
        self.monkeypatch.setenv("SCORINGENGINE_VERSION", "abc1234")
        if "scoring_engine.version" in sys.modules:
            del sys.modules["scoring_engine.version"]
        from scoring_engine.version import BASE_VERSION, version, version_info

        assert version == f"{BASE_VERSION}+abc1234"
        assert version_info["commit"] == "abc1234"
        assert version_info["is_release"] is False

    def test_environment_var_tag_version(self):
        # When SCORINGENGINE_VERSION is a version tag, it's treated as a release
        self.monkeypatch.setenv("SCORINGENGINE_VERSION", "v1.2.0")
        if "scoring_engine.version" in sys.modules:
            del sys.modules["scoring_engine.version"]
        from scoring_engine.version import BASE_VERSION, version, version_info

        assert version == BASE_VERSION
        assert version_info["is_release"] is True
        assert version_info["tag"] == "v1.2.0"

    def test_debug_version(self):
        self.toggle_debug(True)
        if "scoring_engine.version" in sys.modules:
            del sys.modules["scoring_engine.version"]
        from scoring_engine.version import version, version_info

        # Verify it ends with -dev
        assert version.endswith("-dev")
        assert version_info["is_dev"] is True

    def test_debug_env_version(self):
        self.toggle_debug(True)
        self.monkeypatch.setenv("SCORINGENGINE_VERSION", "abcdefg")
        if "scoring_engine.version" in sys.modules:
            del sys.modules["scoring_engine.version"]
        from scoring_engine.version import BASE_VERSION, version, version_info

        assert version == f"{BASE_VERSION}+abcdefg-dev"
        assert version_info["commit"] == "abcdefg"
        assert version_info["is_dev"] is True

    def test_version_info_structure(self):
        if "scoring_engine.version" in sys.modules:
            del sys.modules["scoring_engine.version"]
        from scoring_engine.version import version_info

        # Verify version_info has all expected keys
        assert "base_version" in version_info
        assert "commit" in version_info
        assert "is_release" in version_info
        assert "tag" in version_info
        assert "is_dev" in version_info
        assert "display" in version_info
