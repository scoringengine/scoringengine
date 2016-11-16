import pytest

from redis import Redis

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.engine.job_queue import JobQueue
from scoring_engine.engine.malformed_job import MalformedJob
from scoring_engine.engine.job import Job


class TestJobQueue(object):

    def compare_jobs(self, src_job, dst_job):
        assert isinstance(src_job, Job)
        assert isinstance(dst_job, Job)
        assert src_job.service_id == dst_job.service_id
        assert src_job.command == dst_job.command
        assert src_job.output == dst_job.output

    def setup(self):
        self.queue = JobQueue()
        self.queue.clear()

    def test_init(self):
        assert isinstance(self.queue.conn, Redis) is True
        assert self.queue.queue_name == "jobs"
        assert self.queue.namespace == "scoring_engine"
        assert self.queue.queue_key == "scoring_engine:jobs"
        assert self.queue.size() == 0

    def test_clear(self):
        job = Job(service_id="102938", command="ls -l")
        self.queue.add_job(job)
        assert self.queue.size() == 1
        self.queue.clear()
        assert self.queue.size() == 0

    def test_get_job_without_jobs(self):
        found_job = self.queue.get_job()
        assert found_job is None

    def test_add_job_not_job_class(self):
        with pytest.raises(MalformedJob):
            malformed_job = {"exkey": "exvalue"}
            self.queue.add_job(malformed_job)

    def test_add_job(self):
        job = Job(service_id="12345", command="ls -l")
        self.queue.add_job(job)
        assert self.queue.size() == 1
        found_job = self.queue.get_job()
        self.compare_jobs(found_job, job)
        assert self.queue.size() == 0

    def test_adding_multiple_jobs(self):
        job_1 = Job(service_id="12345", command="ping -c 127.0.0.1")
        job_2 = Job(service_id="54321", command="ping -c 127.0.0.1")
        self.queue.add_job(job_1)
        self.queue.add_job(job_2)
        assert self.queue.size() == 2
        found_job_1 = self.queue.get_job()
        assert self.queue.size() == 1
        found_job_2 = self.queue.get_job()
        self.compare_jobs(found_job_1, job_1)
        self.compare_jobs(found_job_2, job_2)
        assert self.queue.size() == 0
