import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../scoring_engine'))

from worker import Worker
from worker_queue import WorkerQueue
from job import Job


class TestWorker(object):

    def setup(self):
        self.worker = Worker()

    def test_init(self):
        assert isinstance(self.worker.worker_queue, WorkerQueue) is True

    def test_execute_simple_cmd(self):
        job = Job(service_id="12345", command="echo 'HELLO'")
        updated_job = self.worker.execute_cmd(job)
        assert updated_job.output == "HELLO\n"
        assert updated_job.completed() is True
        assert updated_job.passed() is False

    def test_execute_cmd_trigger_timeout(self):
        timeout_time = 1
        sleep_time = timeout_time + 1
        job = Job(service_id="12345", command="sleep " + str(sleep_time))
        updated_job = self.worker.execute_cmd(job, timeout_time)
        assert updated_job.output is None
        assert updated_job.reason == "Command Timed Out"
        assert updated_job.passed() is False
        assert updated_job.completed() is True
