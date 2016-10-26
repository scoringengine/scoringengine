import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../scoring_engine'))

from worker_queue import WorkerQueue

from redis import Redis


class TestWorkerQueue(object):

    def test_init(self):
        queue = WorkerQueue()
        assert isinstance(queue.conn, Redis) is True
        assert queue.queue_name == "scoring_engine-checks"

    def test_add_job(self):
        queue = WorkerQueue()
