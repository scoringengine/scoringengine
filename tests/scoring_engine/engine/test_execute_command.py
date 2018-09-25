import mock

from celery.exceptions import SoftTimeLimitExceeded

from scoring_engine.engine.job import Job
from scoring_engine.engine.execute_command import execute_command


class TestWorker(object):

    def test_basic_run(self):
        job = Job(environment_id="12345", command="echo 'HELLO'")
        task = execute_command.run(job)
        assert task['errored_out'] is False
        assert task['output'] == 'HELLO\n'

    def test_timed_out(self):
        import subprocess
        subprocess.run = mock.Mock(side_effect=SoftTimeLimitExceeded)

        job = Job(environment_id="12345", command="echo 'HELLO'")
        task = execute_command.run(job)
        assert task['errored_out'] is True
