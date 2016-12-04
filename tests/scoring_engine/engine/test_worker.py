import threading
import time

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.engine.worker import Worker
from scoring_engine.engine.worker_queue import WorkerQueue
from scoring_engine.engine.finished_queue import FinishedQueue
from scoring_engine.engine.job import Job


class TestWorker(object):

    def setup(self):
        self.worker = Worker()
        self.worker_queue = WorkerQueue()
        self.worker_queue.clear()
        self.finished_queue = FinishedQueue()
        self.finished_queue.clear()

    def test_init(self):
        assert isinstance(self.worker.worker_queue, WorkerQueue) is True
        assert isinstance(self.worker.finished_queue, FinishedQueue) is True

    def test_shutdown(self):
        assert self.worker.short_circuit is False
        self.worker.shutdown()
        assert self.worker.short_circuit is True

    def test_execute_simple_cmd(self):
        job = Job(environment_id="12345", command="echo 'HELLO'")
        updated_job = self.worker.execute_cmd(job)
        assert updated_job.output == "HELLO\n"
        assert updated_job.completed() is True
        assert updated_job.passed() is False

    def test_execute_cmd_trigger_timeout(self):
        timeout_time = 1
        sleep_time = timeout_time + 1
        job = Job(environment_id="12345", command="sleep " + str(sleep_time))
        updated_job = self.worker.execute_cmd(job, timeout_time)
        assert updated_job.output is None
        assert updated_job.reason == "Command Timed Out"
        assert updated_job.passed() is False
        assert updated_job.completed() is True

    def test_simple_run_one_job(self):
        job = Job(environment_id="12345", command="echo 'HELLO'")
        assert job.output is None
        assert job.completed() is False
        self.worker_queue.add_job(job)
        assert self.finished_queue.get_job() is None
        self.worker.run(1)
        updated_job = self.finished_queue.get_job()
        assert updated_job.environment_id == '12345'
        assert updated_job.command == "echo 'HELLO'"
        assert updated_job.completed() is True
        assert updated_job.passed() is False
        assert updated_job.output == 'HELLO\n'

    def test_simple_run_two_jobs_one_run(self):
        job_1 = Job(environment_id="12345", command="echo 'HELLO'")
        job_2 = Job(environment_id="12345", command="echo 'HI'")
        self.worker_queue.add_job(job_1)
        self.worker_queue.add_job(job_2)
        self.worker.run(1)
        updated_job_1 = self.finished_queue.get_job()
        updated_job_2 = self.finished_queue.get_job()
        assert updated_job_1.environment_id == '12345'
        assert updated_job_1.command == "echo 'HELLO'"
        assert updated_job_1.completed() is True
        assert updated_job_1.passed() is False
        assert updated_job_1.output == 'HELLO\n'
        assert updated_job_2 is None

    def test_simple_run_two_jobs_two_runs(self):
        job_1 = Job(environment_id="12345", command="echo 'HELLO'")
        job_2 = Job(environment_id="54321", command="echo 'HI'")
        self.worker_queue.add_job(job_1)
        self.worker_queue.add_job(job_2)
        self.worker.run(2)
        updated_job_1 = self.finished_queue.get_job()
        updated_job_2 = self.finished_queue.get_job()
        assert updated_job_1.environment_id == '12345'
        assert updated_job_1.command == "echo 'HELLO'"
        assert updated_job_1.completed() is True
        assert updated_job_1.passed() is False
        assert updated_job_1.output == 'HELLO\n'
        assert updated_job_2.environment_id == '54321'
        assert updated_job_2.command == "echo 'HI'"
        assert updated_job_2.completed() is True
        assert updated_job_2.passed() is False
        assert updated_job_2.output == 'HI\n'

    def test_simple_run_three_jobs_unlimited_runs(self):
        job_1 = Job(environment_id="12345", command="echo 'HELLO'")
        job_2 = Job(environment_id="12345", command="echo 'ABC'")
        job_3 = Job(environment_id="54321", command="echo 'HI'")
        self.worker_queue.add_job(job_1)
        self.worker_queue.add_job(job_2)
        self.worker_queue.add_job(job_3)
        # To simulate running all the time, we spawn a thread
        worker_thread = threading.Thread(target=self.worker.run)
        worker_thread.start()

        # then wait a couple seconds, and then tell the worker to stop
        time.sleep(2)
        self.worker.shutdown()

        updated_job_1 = self.finished_queue.get_job()
        assert isinstance(updated_job_1, Job)
        updated_job_2 = self.finished_queue.get_job()
        assert isinstance(updated_job_2, Job)
        updated_job_3 = self.finished_queue.get_job()
        assert isinstance(updated_job_3, Job)
