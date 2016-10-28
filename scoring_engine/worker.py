import subprocess
from worker_queue import WorkerQueue
from config import Config


class Worker(object):

    def __init__(self):
        self.worker_queue = WorkerQueue()
        self.config = Config()

    def execute_cmd(self, job, timeout=None):
        if timeout is None:
            timeout = self.config.check_timeout
        print("Executing " + str(job.command) + " for " + str(job.service_id))
        try:
            output = subprocess.run(job.command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout).stdout.decode("utf-8")
            job.set_output(output)
        except subprocess.TimeoutExpired:
            job.set_fail('Job Timed Out')

        return job
