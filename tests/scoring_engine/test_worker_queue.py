import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../scoring_engine'))

from worker_queue import WorkerQueue

from redis import Redis


class TestWorkerQueue(object):

    def setup(self):
        self.queue = WorkerQueue()
        self.queue.clear()

    def test_init(self):
        assert isinstance(self.queue.conn, Redis) is True
        assert self.queue.queue_name == "checks"
        assert self.queue.namespace == "scoring_engine"
        assert self.queue.queue_key == "scoring_engine:checks"
        assert self.queue.size() == 0

    def test_clear(self):
        self.queue.add_job({"exkey": "exvalue"})
        assert self.queue.size() == 1
        self.queue.clear()
        assert self.queue.size() == 0

    def test_get_job_without_jobs(self):
        found_job = self.queue.get_job()
        assert found_job is None

    def test_add_job(self):
        job_dict = {"service_id": "12345", "command": "ping -c 127.0.0.1"}
        self.queue.add_job(job_dict)
        assert self.queue.size() == 1
        found_job = self.queue.get_job()
        assert found_job == job_dict
        assert self.queue.size() == 0

    def test_adding_multiple_jobs(self):
        job_dict_1 = {"service_id": "12345", "command": "ping -c 127.0.0.1"}
        job_dict_2 = {"service_id": "54321", "command": "ping -c 1.1.1.1"}
        self.queue.add_job(job_dict_1)
        self.queue.add_job(job_dict_2)
        assert self.queue.size() == 2
        found_job_1 = self.queue.get_job()
        assert self.queue.size() == 1
        found_job_2 = self.queue.get_job()
        assert found_job_1 == job_dict_1
        assert found_job_2 == job_dict_2
        assert self.queue.size() == 0
