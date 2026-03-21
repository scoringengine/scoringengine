import subprocess

from celery.exceptions import SoftTimeLimitExceeded

from scoring_engine.celery_app import celery_app
from scoring_engine.logger import logger


@celery_app.task(name="execute_command", acks_late=True, reject_on_worker_lost=True, soft_time_limit=30, time_limit=60)
def execute_command(job):
    output = ""
    # Disable duplicate celery log messages
    if logger.propagate:
        logger.propagate = False
    logger.info("Running cmd for " + str(job))
    try:
        cmd_result = subprocess.run(
            job["command"],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
            start_new_session=True,
        )
        output = cmd_result.stdout.decode("utf-8", errors="replace")
        job["errored_out"] = False
    except subprocess.TimeoutExpired as e:
        job["errored_out"] = True
        if e.output:
            output = e.output.decode("utf-8", errors="replace")
    except SoftTimeLimitExceeded:
        job["errored_out"] = True
    # Cap output stored in Redis to avoid bloating Celery result backend.
    # Large outputs (e.g. full HTML pages from HTTP checks) cause massive
    # serialization overhead on every AsyncResult.state/.result call.
    MAX_OUTPUT = 10000
    job["output"] = output[:MAX_OUTPUT]
    return job
