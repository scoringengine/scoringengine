import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.engine.execute_command import execute_command
from scoring_engine.engine.job import Job


class TestWorker(object):

    def test_basic_run(self):
        job = Job(environment_id="12345", command="echo 'HELLO'")
        task = execute_command.run(job)
        assert task['errored_out'] is False
        assert task['output'] == 'HELLO\n'

    def test_timed_out(self):
        # this is a weak unit test, but I couldn't figure out
        # how to run the job without a worker and still
        # honor the soft timeout
        assert execute_command.soft_time_limit == 30
