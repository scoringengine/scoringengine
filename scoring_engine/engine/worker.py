import subprocess
from functools import partial
import signal
import time

from scoring_engine.engine.worker_queue import WorkerQueue
from scoring_engine.engine.finished_queue import FinishedQueue
from scoring_engine.engine.config import Config


def worker_sigint_handler(signum, frame, worker_obj=None):
    if worker_obj is not None:
        worker_obj.shutdown()


class Worker(object):

    def __init__(self):
        self.worker_queue = WorkerQueue()
        self.finished_queue = FinishedQueue()
        self.config = Config()
        self.short_circuit = False
        signal.signal(signal.SIGINT, partial(worker_sigint_handler, obj=self))
        signal.signal(signal.SIGTERM, partial(worker_sigint_handler, obj=self))

    def shutdown(self):
        print("Shutting down worker...")
        self.short_circuit = True

    def execute_cmd(self, job, timeout=None):
        if timeout is None:
            timeout = self.config.check_timeout
        print("Executing " + str(job.command) + " for " + str(job.service_id))
        try:
            cmd_result = subprocess.run(
                job.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=timeout
            )
            output = cmd_result.stdout.decode("utf-8")
            job.set_output(output)
        except subprocess.TimeoutExpired:
            job.set_fail('Command Timed Out')

        return job

    def run(self, total_times=-1):
        num_times = 0
        while num_times != total_times and not self.short_circuit:
            print("Looking for work...")
            num_times += 1
            retrieved_job = self.worker_queue.get_job()
            if retrieved_job is None:
                try:
                    time.sleep(5)
                except Exception:
                    self.shutdown()
                    pass
                continue
            updated_job = self.execute_cmd(retrieved_job)
            self.finished_queue.add_job(updated_job)
