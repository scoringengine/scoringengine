import os
import signal
import subprocess

from celery.exceptions import SoftTimeLimitExceeded

from scoring_engine.celery_app import celery_app
from scoring_engine.logger import logger

# Subprocess wall-clock timeout for a single check, in seconds. Kept below the
# Celery soft_time_limit so we normally hit this (and clean up the process group)
# before Celery raises SoftTimeLimitExceeded into the task.
CMD_TIMEOUT = 30


def _kill_process_group(proc):
    """SIGKILL the whole session/process group of ``proc``.

    The check runs with ``start_new_session=True``, which makes the shell a
    session/group leader. Signalling only the shell (what ``subprocess.run``'s
    timeout does, and what ``proc.kill()`` does) leaves the shell's own children --
    the actual hung check command (ssh, curl, xfreerdp, a browser, ...) -- alive.
    Those get reparented to PID 1; in the worker container PID 1 is the Celery
    worker itself, which never reaps them, so they pile up (this was a real,
    days-long process leak). Killing the group takes the children with it.
    """
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        # Already gone, or we cannot signal it -- nothing more to do here.
        pass


@celery_app.task(name="execute_command", acks_late=True, reject_on_worker_lost=True, soft_time_limit=30, time_limit=60)
def execute_command(job):
    output = ""
    # Disable duplicate celery log messages
    if logger.propagate:
        logger.propagate = False
    # Never log the command itself: it contains plaintext service credentials.
    logger.info("Running check for environment %s", job.get("environment_id", "<dry-run>"))

    # Popen (rather than subprocess.run) so we hold the pid and can kill the whole
    # process group on timeout -- see _kill_process_group.
    # Check credentials arrive as env vars (see basic_check.Secret) so they never
    # appear in the command string that gets logged and stored.
    env = None
    if job.get("env"):
        env = dict(os.environ)
        env.update(job["env"])

    proc = subprocess.Popen(
        job["command"],
        shell=True,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    try:
        stdout, _ = proc.communicate(timeout=CMD_TIMEOUT)
        output = stdout.decode("utf-8", errors="replace")
        job["errored_out"] = False
    except subprocess.TimeoutExpired:
        job["errored_out"] = True
        _kill_process_group(proc)
        # Drain any partial output and reap the group leader.
        try:
            stdout, _ = proc.communicate(timeout=5)
            if stdout:
                output = stdout.decode("utf-8", errors="replace")
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    except SoftTimeLimitExceeded:
        # Celery's soft limit fired first; still tear down the whole group.
        job["errored_out"] = True
        _kill_process_group(proc)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    finally:
        # Belt and suspenders: never return with the group still running.
        if proc.poll() is None:
            _kill_process_group(proc)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass

    # Cap output stored in Redis to avoid bloating Celery result backend.
    # Large outputs (e.g. full HTML pages from HTTP checks) cause massive
    # serialization overhead on every AsyncResult.state/.result call.
    MAX_OUTPUT = 5000
    job["output"] = output[:MAX_OUTPUT]
    # Don't echo credentials back into the result backend.
    job.pop("env", None)
    return job
