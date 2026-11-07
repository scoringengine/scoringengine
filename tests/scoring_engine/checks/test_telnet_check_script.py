"""Run bin/telnet_check against an in-process fake telnet server."""

import os
import socket
import subprocess
import sys
import threading

import pytest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "scoring_engine", "checks", "bin", "telnet_check")
IAC, DONT, DO, WONT, WILL = 255, 254, 253, 252, 251
ECHO, SGA = 1, 3


class FakeTelnetServer:
    def __init__(self, password="secret", send_login_prompt=True):
        self.password = password
        self.send_login_prompt = send_login_prompt
        self.negotiation_replies = b""
        self.commands = []
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(5)
        self.port = self.sock.getsockname()[1]
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _readline(self, conn):
        data = b""
        while not data.endswith(b"\n"):
            chunk = conn.recv(1)
            if not chunk:
                break
            if chunk[0] == IAC:
                self.negotiation_replies += chunk + conn.recv(2)
                continue
            data += chunk
        return data.strip().decode()

    def _serve(self):
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            with conn:
                # Offer options the client should refuse, then prompt
                conn.sendall(bytes([IAC, DO, ECHO, IAC, WILL, SGA]) + b"Debian GNU/Linux 12\r\n")
                if not self.send_login_prompt:
                    while conn.recv(1024):  # stay silent until the client gives up
                        pass
                    continue
                conn.sendall(b"web01 login: ")
                self._readline(conn)
                conn.sendall(b"Password: ")
                if self._readline(conn) != self.password:
                    conn.sendall(b"\r\nLogin incorrect\r\n")
                    continue
                conn.sendall(b"\r\nuser@web01:~$ ")
                command = self._readline(conn)
                self.commands.append(command)
                conn.sendall("output-of[{0}]\r\nuser@web01:~$ ".format(command).encode())
                self._readline(conn)  # exit
                conn.sendall(b"logout\r\n")

    def close(self):
        self.sock.close()


def _run(port, password="secret", commands="id", timeout="3"):
    result = subprocess.run(
        [sys.executable, SCRIPT, "127.0.0.1", str(port), timeout, "user", password, commands],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.returncode, result.stdout


@pytest.fixture
def server():
    srv = FakeTelnetServer()
    yield srv
    srv.close()


class TestTelnetCheckScript:
    def test_runs_each_command_in_its_own_session(self, server):
        code, out = _run(server.port, commands="id;whoami")
        assert code == 0
        assert out.startswith("SUCCESS\n")
        assert "output-of[whoami]" in out  # last command's output is printed
        assert server.commands == ["id", "whoami"]

    def test_refuses_offered_options(self, server):
        _run(server.port)
        assert bytes([IAC, WONT, ECHO]) in server.negotiation_replies
        assert bytes([IAC, DONT, SGA]) in server.negotiation_replies

    def test_wrong_password_fails(self, server):
        code, out = _run(server.port, password="wrong")
        assert code == 1
        assert "Failed: Authentication failed" in out
        assert "SUCCESS" not in out

    def test_missing_login_prompt_times_out(self):
        srv = FakeTelnetServer(send_login_prompt=False)
        try:
            code, out = _run(srv.port, timeout="1")
        finally:
            srv.close()
        assert code == 1
        assert "Timed out waiting for login prompt" in out

    def test_connection_refused_fails(self):
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        code, out = _run(port)
        assert code == 1
        assert out.startswith("Failed:")
