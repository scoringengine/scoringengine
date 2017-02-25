from scoring_engine.engine.job import Job


class TestJob(object):

    def setup(self):
        self.job = Job(environment_id="12345", command="ls -l")

    def test_init(self):
        assert self.job['environment_id'] == "12345"
        assert self.job['command'] == "ls -l"

    def test_errored_out(self):
        self.job['errored_out'] = True
        assert self.job['errored_out'] is True
