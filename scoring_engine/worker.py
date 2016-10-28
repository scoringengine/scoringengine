import subprocess
import signal

from worker_queue import WorkerQueue
from finished_queue import FinishedQueue
from config import Config


class Worker(object):

    def __init__(self):
        self.worker_queue = WorkerQueue()
        self.finished_queue = FinishedQueue()
        self.config = Config()
        self.short_circuit = False

        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def shutdown(self):
        self.short_circuit = True

    def execute_cmd(self, job, timeout=None):
        if timeout is None:
            timeout = self.config.check_timeout
        print("Executing " + str(job.command) + " for " + str(job.service_id))
        try:
            cmd_result = subprocess.run(job.command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
            output = cmd_result.stdout.decode("utf-8")
            job.set_output(output)
        except subprocess.TimeoutExpired:
            job.set_fail('Command Timed Out')

        return job

    def run(self, total_times=-1):
        num_times = 0
        while num_times != total_times and not self.short_circuit:
            num_times += 1
            retrieved_job = self.worker_queue.get_job()
            if retrieved_job is None:
                # todo block based on get_job
                continue
            updated_job = self.execute_cmd(retrieved_job)
            self.finished_queue.add_job(updated_job)
