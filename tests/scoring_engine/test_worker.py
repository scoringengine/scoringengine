import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../scoring_engine'))

from worker import Worker
from worker_queue import WorkerQueue


class TestWorker(object):

    def test_init(self):
        worker = Worker()
        assert isinstance(worker.worker_queue, WorkerQueue) is True
