import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../scoring_engine'))

from job import Job


class TestJob(object):

    def test_init_without_output(self):
        job = Job(service_id="12345", command="ls -l")
        assert job.service_id == "12345"
        assert job.command == "ls -l"
        assert job.output is None

    def test_init_with_output(self):
        cmd_output = "-rw-r--r--  1 root  root  0 Oct 26 15:56 abc"
        job = Job(service_id="12345", command="ls -l", output=cmd_output)
        assert job.service_id == "12345"
        assert job.command == "ls -l"
        assert job.output == cmd_output

    def test_add_output(self):
        cmd_output = "-rw-r--r--  1 root  root  0 Oct 26 15:56 abc"
        job = Job(service_id="12345", command="ls -l")
        assert job.service_id == "12345"
        assert job.command == "ls -l"
        assert job.output is None
        job.output = cmd_output
        assert job.output == cmd_output

    def test_to_dict(self):
        cmd_output = "-rw-r--r--  1 root  root  0 Oct 26 15:56 abc"
        job = Job(service_id="12345", command="ls -l", output=cmd_output)
        expected_dict = {
            'service_id': '12345',
            'command': 'ls -l',
            'output': '-rw-r--r--  1 root  root  0 Oct 26 15:56 abc'
        }
        assert job.to_dict() == expected_dict

    def test_from_dict(self):
        cmd_output = "-rw-r--r--  1 root  root  0 Oct 26 15:56 abc"
        input_dict = {
            'service_id': '12345',
            'command': 'ls -l',
            'output': cmd_output
        }
        returned_job = Job.from_dict(input_dict)
        assert isinstance(returned_job, Job)
        assert returned_job.service_id == "12345"
        assert returned_job.command == "ls -l"
        assert returned_job.output == cmd_output
