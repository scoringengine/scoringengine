"""Tests for bin/install -- the guided .env writer.

bin/install has no ``.py`` extension (it lives in ``bin/`` with the other entry
points), so it is loaded from its path rather than imported by name.
"""

import importlib.machinery
import importlib.util
import os
import re
from types import SimpleNamespace

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The variables docker-compose.yml interpolates, plus the Flask key. If this list
# drifts from the compose file the generated .env stops working, so it is the
# contract these tests defend.
COMPOSE_VARS = [
    "PYTHON_VERSION",
    "REDIS_VERSION",
    "MARIADB_VERSION",
    "NGINX_VERSION",
    "MYSQL_ROOT_PASSWORD",
    "MYSQL_PASSWORD",
    "SCORINGENGINE_SECRET_KEY",
]


def _load_installer():
    # bin/install has no .py suffix, so importlib can't infer a loader from the
    # path -- give it an explicit source loader.
    path = os.path.join(REPO_ROOT, "bin", "install")
    loader = importlib.machinery.SourceFileLoader("bin_install", path)
    spec = importlib.util.spec_from_loader("bin_install", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


install = _load_installer()


def _parse_env(text):
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        out[key] = value
    return out


class TestInstaller:
    def test_build_env_includes_every_compose_variable(self):
        env = _parse_env(install.build_env({v: "x" for v in COMPOSE_VARS}))
        assert set(COMPOSE_VARS) <= set(env)

    def test_non_interactive_writes_a_valid_env(self, tmp_path):
        target = tmp_path / ".env"
        assert install.main(["--non-interactive", "--env-path", str(target)]) == 0
        env = _parse_env(target.read_text())
        for var in COMPOSE_VARS:
            assert env.get(var), f"{var} missing or empty"
        # A freshly generated 128-hex-char Flask key.
        assert re.fullmatch(r"[0-9a-f]{128}", env["SCORINGENGINE_SECRET_KEY"])
        # Image versions default to the .env.example values.
        assert env["REDIS_VERSION"] == install.IMAGE_DEFAULTS["REDIS_VERSION"]

    def test_generated_passwords_are_env_safe(self, tmp_path):
        target = tmp_path / ".env"
        install.main(["--non-interactive", "--env-path", str(target)])
        env = _parse_env(target.read_text())
        # token_urlsafe alphabet only: no '#', '=', quotes or spaces to break .env/URIs.
        for var in ("MYSQL_ROOT_PASSWORD", "MYSQL_PASSWORD"):
            assert re.fullmatch(r"[A-Za-z0-9_-]+", env[var]), env[var]

    def test_refuses_to_overwrite_without_force(self, tmp_path):
        target = tmp_path / ".env"
        target.write_text("EXISTING=1\n")
        assert install.main(["--non-interactive", "--env-path", str(target)]) == 1
        assert target.read_text() == "EXISTING=1\n"

    def test_force_overwrites(self, tmp_path):
        target = tmp_path / ".env"
        target.write_text("EXISTING=1\n")
        assert install.main(["--non-interactive", "--force", "--env-path", str(target)]) == 0
        body = target.read_text()
        assert "EXISTING" not in body
        assert "MYSQL_PASSWORD" in body

    def test_supplied_values_are_used_verbatim(self, tmp_path):
        target = tmp_path / ".env"
        install.main(
            [
                "--non-interactive",
                "--env-path",
                str(target),
                "--mysql-password",
                "app-secret-123",
                "--mysql-root-password",
                "root-secret-456",
                "--secret-key",
                "deadbeef",
            ]
        )
        env = _parse_env(target.read_text())
        assert env["MYSQL_PASSWORD"] == "app-secret-123"
        assert env["MYSQL_ROOT_PASSWORD"] == "root-secret-456"
        assert env["SCORINGENGINE_SECRET_KEY"] == "deadbeef"

    def test_interactive_answers_override_generated_defaults(self):
        # Four blank answers accept the version defaults, then explicit secrets.
        answers = iter(["", "", "", "", "my-root", "my-app", "my-secret", ""])
        args = SimpleNamespace(mysql_root_password=None, mysql_password=None, secret_key=None)
        values = install.collect(args, interactive=True, prompt=lambda _p: next(answers))
        assert values["MYSQL_ROOT_PASSWORD"] == "my-root"
        assert values["MYSQL_PASSWORD"] == "my-app"
        assert values["SCORINGENGINE_SECRET_KEY"] == "my-secret"
        assert values["REDIS_VERSION"] == install.IMAGE_DEFAULTS["REDIS_VERSION"]


class TestInstallerPacks:
    def test_default_is_core_worker_only(self, tmp_path):
        target = tmp_path / ".env"
        assert install.main(["--non-interactive", "--env-path", str(target)]) == 0
        env = _parse_env(target.read_text())
        assert env["WORKER_TARGET"] == "core"
        assert env["COMPOSE_PROFILES"] == ""

    def test_all_selects_single_full_worker(self, tmp_path):
        target = tmp_path / ".env"
        assert install.main(["--non-interactive", "--env-path", str(target), "--packs", "all"]) == 0
        env = _parse_env(target.read_text())
        assert env["WORKER_TARGET"] == "full"
        assert env["COMPOSE_PROFILES"] == ""

    def test_packs_select_core_worker_and_profiles(self, tmp_path):
        target = tmp_path / ".env"
        assert install.main(["--non-interactive", "--env-path", str(target), "--packs", "browser, db"]) == 0
        env = _parse_env(target.read_text())
        assert env["WORKER_TARGET"] == "core"
        assert env["COMPOSE_PROFILES"] == "db,browser"

    def test_core_only(self, tmp_path):
        target = tmp_path / ".env"
        assert install.main(["--non-interactive", "--env-path", str(target), "--packs", "core"]) == 0
        env = _parse_env(target.read_text())
        assert env["WORKER_TARGET"] == "core"
        assert env["COMPOSE_PROFILES"] == ""

    def test_unknown_pack_is_rejected(self, tmp_path):
        target = tmp_path / ".env"
        assert install.main(["--non-interactive", "--env-path", str(target), "--packs", "gpu"]) == 2
        assert not target.exists()

    def test_interactive_reprompts_on_bad_pack(self):
        answers = iter(["", "", "", "", "", "", "", "gpu", "rdp"])
        args = SimpleNamespace(mysql_root_password=None, mysql_password=None, secret_key=None, packs=None)
        values = install.collect(args, interactive=True, prompt=lambda _p: next(answers))
        assert values["WORKER_PACKS"] == ["rdp"]

    def test_optional_packs_match_worker_packs(self):
        from scoring_engine.worker_packs import DEFAULT_PACK, PACKS

        assert set(install.OPTIONAL_PACKS) == set(PACKS) - {DEFAULT_PACK}
