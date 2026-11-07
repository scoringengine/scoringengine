"""Tests for the check subprocess runner.

The load-bearing tests here are the process-group ones: a check that spawns a
child and then hangs must have that child killed when the check times out. Before
the fix, ``start_new_session=True`` plus a timeout that only signalled the direct
child left the grandchild orphaned to PID 1, where the Celery worker never reaped
it -- a days-long process leak in production.
"""

import subprocess
import time
from unittest import mock

from celery.exceptions import SoftTimeLimitExceeded

import scoring_engine.engine.execute_command as ec
from scoring_engine.engine.execute_command import _kill_process_group, execute_command
from scoring_engine.engine.job import Job


def _proc_state(pid):
    """Linux process state for pid: 'R'/'S'/'D' alive, 'Z' zombie, None gone."""
    try:
        with open("/proc/{0}/stat".format(pid)) as fh:
            # comm may contain spaces/parens; state is the field right after ')'.
            return fh.read().rsplit(")", 1)[1].split()[0]
    except (FileNotFoundError, ProcessLookupError):
        return None


def _wait_dead(pid, timeout=5.0):
    """True once pid is gone or a zombie (i.e. no longer running)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        state = _proc_state(pid)
        if state is None or state == "Z":
            return True
        time.sleep(0.05)
    return False


class TestWorker:
    def test_basic_run(self):
        job = Job(environment_id="12345", command="echo 'HELLO'")
        task = execute_command.run(job)
        assert task["errored_out"] is False
        assert task["output"] == "HELLO\n"

    def test_soft_time_limit_still_marks_errored(self):
        # Celery raising its soft limit into the task must still flag the job and
        # not raise out of the task.
        real_popen = subprocess.Popen

        class _Proc:
            def __init__(self, *a, **k):
                self._p = real_popen("sleep 0", shell=True, start_new_session=True)
                self.pid = self._p.pid

            def communicate(self, timeout=None):
                raise SoftTimeLimitExceeded()

            def wait(self, timeout=None):
                return self._p.wait(timeout=timeout)

            def poll(self):
                return self._p.poll()

            def kill(self):
                self._p.kill()

        with mock.patch.object(subprocess, "Popen", _Proc):
            job = Job(environment_id="12345", command="echo hi")
            task = execute_command.run(job)
        assert task["errored_out"] is True


class TestProcessGroupCleanup:
    def test_kill_process_group_kills_grandchild(self):
        # Shell backgrounds a long sleep (the "grandchild") and prints its pid,
        # then blocks. start_new_session makes the shell a group leader.
        proc = subprocess.Popen(
            "sleep 60 & echo $!; wait",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        grandchild_pid = int(proc.stdout.readline().strip())
        assert _proc_state(grandchild_pid) in ("R", "S", "D")  # alive

        _kill_process_group(proc)
        proc.wait(timeout=5)

        assert _wait_dead(grandchild_pid), "grandchild survived the group kill"

    def test_timeout_reaps_the_whole_group(self, monkeypatch):
        # Drive the real timeout path fast. Old code (kill only the direct child)
        # would leave the backgrounded sleep alive; the fix kills the group.
        monkeypatch.setattr(ec, "CMD_TIMEOUT", 0.4)
        job = Job(environment_id="12345", command="sleep 60 & echo GC:$!; wait")
        task = execute_command.run(job)

        assert task["errored_out"] is True
        assert "GC:" in task["output"]
        grandchild_pid = int(task["output"].split("GC:")[1].split()[0])
        assert _wait_dead(grandchild_pid), "grandchild survived the check timeout"


class TestCredentialsNotLogged:
    def test_command_with_password_is_not_logged(self):
        job = Job(environment_id=7, command="echo -p 'Sup3rS3cret!'")
        with mock.patch.object(ec, "logger") as mock_logger:
            mock_logger.propagate = False
            result = execute_command(job)
        assert "Sup3rS3cret!" in result["output"]
        logged = " ".join(str(c) for c in mock_logger.mock_calls)
        assert "Sup3rS3cret!" not in logged
        mock_logger.info.assert_any_call("Running check for environment %s", 7)
