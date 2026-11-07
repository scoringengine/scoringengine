import os
import shlex
import subprocess

import yaml

from scoring_engine.checks.adcs_web_enroll import ADCSWebEnrollCheck

REPO = os.path.join(os.path.dirname(__file__), "..", "..", "..")


def _render(*args):
    return ADCSWebEnrollCheck.CMD.format(*[shlex.quote(a) for a in args])


class TestADCSWebEnrollOptional:
    def test_reports_missing_certipy(self, tmp_path):
        cmd = _render("jdoe@corp.local", "pw", "127.0.0.1", "corp-CA", "User")
        # PATH without certipy (only the empty tmp dir plus basic system tools)
        env = {"PATH": f"{tmp_path}:/usr/bin:/bin"}
        out = subprocess.run(["sh", "-c", cmd], capture_output=True, text=True, env=env, timeout=10).stdout
        assert "certipy is not installed in the worker image; enable the adcs worker pack" in out
        assert "Got certificate" not in out

    def test_runs_certipy_when_installed(self, tmp_path):
        fake = tmp_path / "certipy"
        fake.write_text('#!/bin/sh\necho "args: $*"\necho "[*] Got certificate with UPN \'jdoe@corp.local\'"\n')
        fake.chmod(0o755)
        cmd = _render("jdoe@corp.local", "pw", "10.0.0.5", "corp-CA", "User")
        env = {"PATH": f"{tmp_path}:/usr/bin:/bin", "TMPDIR": str(tmp_path)}
        out = subprocess.run(["sh", "-c", cmd], capture_output=True, text=True, env=env, timeout=10).stdout
        assert "Got certificate" in out
        assert "-ca corp-CA -template User -web" in out
        # temp dir for requested certs/keys is cleaned up
        assert sorted(p.name for p in tmp_path.iterdir()) == ["certipy"]

    def test_certipy_is_an_opt_in_worker_pack(self):
        assert ADCSWebEnrollCheck.REQUIRES_PACK == "adcs"
        with open(os.path.join(REPO, "docker-compose.yml")) as f:
            services = yaml.safe_load(f)["services"]
        assert services["worker-adcs"]["profiles"] == ["adcs"]
        with open(os.path.join(REPO, "docker", "worker", "Dockerfile")) as f:
            dockerfile = f.read()
        core_stage = dockerfile.split("AS core-deps\n", 1)[1].split("\nFROM ", 1)[0]
        assert "adcs.sh" not in core_stage
