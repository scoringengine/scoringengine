import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../scoring_engine'))

from finished_queue import FinishedQueue
from job_queue import JobQueue


class TestFinishedQueue(object):

    def test_init(self):
        queue = FinishedQueue()
        assert isinstance(queue, JobQueue) is True
        assert queue.queue_name == "finished"
        assert queue.queue_key == "scoring_engine:finished"
