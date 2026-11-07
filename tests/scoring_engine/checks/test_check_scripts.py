"""Run the smb_check / ssh_check scripts against stub client libraries.

pysmb and paramiko are worker-only dependencies, so the scripts are executed
as subprocesses with stub modules placed first on PYTHONPATH.
"""

import hashlib
import os
import socket
import subprocess
import sys
import textwrap

import pytest

BIN_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "scoring_engine", "checks", "bin")

SMB_STUB = """
import os
SHARES = os.environ["STUB_SHARES"].split(",")
CONTENT = os.environ["STUB_CONTENT"].encode()

class _Share:
    def __init__(self, name):
        self.name = name

class SMBConnection:
    def __init__(self, *args, **kwargs):
        pass
    def connect(self, host, port, timeout=None):
        return True
    def listShares(self):
        return [_Share(n) for n in SHARES]
    def retrieveFile(self, share, path, fileobj):
        fileobj.write(CONTENT)
"""

PARAMIKO_STUB = """
class AuthenticationException(Exception):
    pass

class SSHException(Exception):
    pass

class ChannelException(SSHException):
    pass

class AutoAddPolicy:
    pass

class SSHClient:
    def set_missing_host_key_policy(self, policy):
        pass
    def connect(self, **kwargs):
        pass
    def exec_command(self, command, timeout=None):
        raise ChannelException("Administratively prohibited")
    def close(self):
        pass
"""


@pytest.fixture
def stub_path(tmp_path):
    (tmp_path / "smb").mkdir()
    (tmp_path / "smb" / "__init__.py").write_text("")
    (tmp_path / "smb" / "SMBConnection.py").write_text(textwrap.dedent(SMB_STUB))
    (tmp_path / "paramiko.py").write_text(textwrap.dedent(PARAMIKO_STUB))
    return str(tmp_path)


def _run(script, args, stub_path, **env):
    full_env = dict(os.environ, PYTHONPATH=stub_path, **env)
    result = subprocess.run(
        [sys.executable, os.path.join(BIN_DIR, script), *args],
        capture_output=True,
        text=True,
        env=full_env,
        timeout=30,
    )
    return result.stdout


class TestSMBCheckScript:
    def _smb(self, stub_path, share, content, expected_hash, shares="IPC$,files"):
        args = ["--host", "127.0.0.1", "--port", "445", "--user", "u", "--pass", "p"]
        args += ["--remote-name", "dc", "--share", share, "--file", "flag.txt", "--hash", expected_hash]
        return _run("smb_check", args, stub_path, STUB_SHARES=shares, STUB_CONTENT=content)

    def test_success(self, stub_path):
        out = self._smb(stub_path, "files", "hello", hashlib.sha256(b"hello").hexdigest())
        assert "SUCCESS" in out

    def test_missing_share_lists_available_shares(self, stub_path):
        out = self._smb(stub_path, "backups", "hello", "x")
        assert "Share 'backups' not found. Available shares: IPC$, files" in out
        assert "SUCCESS" not in out

    def test_hash_mismatch_is_reported_without_leaking_expected_hash(self, stub_path):
        expected = hashlib.sha256(b"original").hexdigest()
        out = self._smb(stub_path, "files", "tampered", expected)
        assert "File 'flag.txt' content does not match the expected hash" in out
        assert expected not in out
        assert "SUCCESS" not in out


class TestSSHCheckScript:
    def test_channel_open_failure_reports_clean_step(self, stub_path):
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = str(listener.getsockname()[1])
        try:
            out = _run("ssh_check", ["127.0.0.1", port, "u", "p", "id"], stub_path)
        finally:
            listener.close()
        assert "[-] Command 1/1: could not run command: ChannelException: Administratively prohibited" in out
        assert "Traceback" not in out
        assert "SUCCESS" not in out
