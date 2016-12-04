import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.engine.job import Job


class TestJob(object):

    def setup(self):
        self.job = Job(environment_id="12345", command="ls -l")

    def test_init(self):
        assert self.job.environment_id == "12345"
        assert self.job.command == "ls -l"
        assert self.job.output is None
        assert self.job.result is None
        assert self.job.reason is None
        assert self.job.passed() is False
        assert self.job.completed() is False

    def test_add_output(self):
        cmd_output = "-rw-r--r--  1 root  root  0 Oct 26 15:56 abc"
        assert self.job.environment_id == "12345"
        assert self.job.command == "ls -l"
        assert self.job.output is None
        assert self.job.result is None
        self.job.set_output(cmd_output)
        assert self.job.output == cmd_output
        assert self.job.passed() is False
        assert self.job.completed() is True

    def test_to_dict_without_output_result(self):
        expected_dict = {
            'environment_id': '12345',
            'command': 'ls -l',
            "finished": False,
        }
        assert self.job.to_dict() == expected_dict

    def test_to_dict_with_output_without_result(self):
        self.job.set_output("example output")
        expected_dict = {
            'environment_id': '12345',
            'command': 'ls -l',
            "finished": True,
            "output": "example output"
        }
        assert self.job.to_dict() == expected_dict

    def test_to_dict_with_output_result_pass(self):
        self.job.set_output("example output")
        self.job.set_pass()
        expected_dict = {
            'environment_id': '12345',
            'command': 'ls -l',
            "finished": True,
            "output": "example output",
            "result": "Pass",
        }
        assert self.job.to_dict() == expected_dict

    def test_to_dict_with_output_result_fail(self):
        self.job.set_output("example output")
        self.job.set_fail('No Match')
        expected_dict = {
            'environment_id': '12345',
            'command': 'ls -l',
            "finished": True,
            "output": "example output",
            "result": "Fail",
            "reason": 'No Match'
        }
        assert self.job.to_dict() == expected_dict

    def test_pass_job(self):
        assert self.job.completed() is False
        assert self.job.passed() is False
        self.job.set_output("example output")
        self.job.set_pass()
        assert self.job.completed() is True
        assert self.job.passed() is True

    def test_fail_job_without_output(self):
        assert self.job.completed() is False
        assert self.job.passed() is False
        assert self.job.output is None
        self.job.set_fail('Timed out')
        assert self.job.output is None
        assert self.job.completed() is True
        assert self.job.passed() is False

    def test_fail_job_with_output(self):
        assert self.job.completed() is False
        assert self.job.passed() is False
        assert self.job.output is None
        self.job.set_output('Example output')
        self.job.set_fail('No Match')
        assert self.job.output == 'Example output'
        assert self.job.completed() is True
        assert self.job.passed() is False

    def test_from_dict_with_unfinished_job(self):
        input_dict = {
            'environment_id': '12345',
            'command': 'ls -l',
        }
        returned_job = Job.from_dict(input_dict)
        assert isinstance(returned_job, Job)
        assert returned_job.environment_id == "12345"
        assert returned_job.command == "ls -l"
        assert returned_job.passed() is False
        assert returned_job.completed() is False

    def test_from_dict_with_passed_job(self):
        input_dict = {
            'environment_id': '12345',
            'command': 'ls -l',
            'output': 'example output',
            'result': 'Pass',
            'finished': True
        }
        returned_job = Job.from_dict(input_dict)
        assert isinstance(returned_job, Job)
        assert returned_job.environment_id == "12345"
        assert returned_job.command == "ls -l"
        assert returned_job.output == 'example output'
        assert returned_job.passed() is True
        assert returned_job.completed() is True

    def test_from_dict_with_failed_job(self):
        input_dict = {
            'environment_id': '12345',
            'command': 'ls -l',
            'output': 'example output',
            'result': 'Fail',
            'finished': True,
            'reason': 'No Match'
        }
        returned_job = Job.from_dict(input_dict)
        assert isinstance(returned_job, Job)
        assert returned_job.environment_id == "12345"
        assert returned_job.command == "ls -l"
        assert returned_job.output == 'example output'
        assert returned_job.reason == 'No Match'
        assert returned_job.passed() is False
        assert returned_job.completed() is True

    def test_from_dict_with_timed_out_job(self):
        input_dict = {
            'environment_id': '12345',
            'command': 'ls -l',
            'result': 'Fail',
            'finished': True,
            'reason': 'Timed Out'
        }
        returned_job = Job.from_dict(input_dict)
        assert isinstance(returned_job, Job)
        assert returned_job.environment_id == "12345"
        assert returned_job.command == "ls -l"
        assert returned_job.reason == 'Timed Out'
        assert returned_job.passed() is False
        assert returned_job.completed() is True
