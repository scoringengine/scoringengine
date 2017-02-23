from scoring_engine.celery_app import celery_app
from billiard.exceptions import SoftTimeLimitExceeded
import subprocess

from scoring_engine.logger import logger


@celery_app.task(name='execute_command', soft_time_limit=30)
def execute_command(job):
    output = ""
    logger.info("Running cmd for " + str(job))
    try:
        cmd_result = subprocess.run(
            job['command'],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        output = cmd_result.stdout.decode("utf-8")
        job['errored_out'] = False
    except SoftTimeLimitExceeded:
        job['errored_out'] = True
    job['output'] = output
    return job
