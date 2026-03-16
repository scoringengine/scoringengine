from scoring_engine.celery_app import celery_app
from celery.exceptions import SoftTimeLimitExceeded
import os
import subprocess
from scoring_engine.logger import logger

@celery_app.task(
    name='execute_command',
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True,
    soft_time_limit=30
)
def execute_command(self, job):
    output = ""
    # Disable duplicate celery log messages
    if logger.propagate:
        logger.propagate = False
    
    logger.info(
        "Running command",
        extra={
            "job": str(job),
            "task_id": self.request.id 
        }
    )
    
    try:
        # Pass environment variables from job to subprocess if present.
        # This allows checks to pass sensitive data (e.g. passwords) via
        # env vars instead of command-line arguments, avoiding shell
        # interpretation issues with special characters.
        env = None
        if job.get('env'):
            env = os.environ.copy()
            env.update(job['env'])

        cmd_result = subprocess.run(
            job['command'],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env
        )
        output = cmd_result.stdout.decode("utf-8")
        job['errored_out'] = False
        
    except SoftTimeLimitExceeded:
        job['errored_out'] = True
        output = "Task execution timed out"
        
        logger.warning(
            "Task timed out",
            extra={
                "task_id": self.request.id,
                "job": str(job)
            }
        )
    
    job['output'] = output
    job.pop('env', None)

    logger.info(
        "Command completed",
        extra={
            "task_id": self.request.id,
            "errored_out": job['errored_out']
        }
    )

    return job