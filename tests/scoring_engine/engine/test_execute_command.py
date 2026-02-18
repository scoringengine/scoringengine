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

    @mock.patch('subprocess.run', side_effect=SoftTimeLimitExceeded)
    def test_timed_out(self, mock_subprocess_run):
        job = Job(environment_id="12345", command="echo 'HELLO'")
        task = execute_command.run(job)
        assert task['errored_out'] is True

    def test_env_vars_passed_to_subprocess(self):
        job = Job(
            environment_id="12345",
            command='python -c "import os; print(os.environ.get(\'SCORING_PASSWORD\', \'\'), end=\'\')"',
            env={"SCORING_PASSWORD": "p@ss_w0rd"}
        )
        task = execute_command.run(job)
        assert task['errored_out'] is False
        assert task['output'] == "p@ss_w0rd"

    def test_env_vars_special_chars(self):
        """Verify passwords with shell-dangerous characters survive via env var."""
        special_passwords = [
            "pass'word",
            'pass"word',
            "pass\\word",
            "p@ss$word!&|;",
            "pass word with spaces",
            "p!a#s%s^w&o*r(d)",
        ]
        for password in special_passwords:
            job = Job(
                environment_id="12345",
                command='python -c "import os, sys; sys.stdout.write(os.environ[\'SCORING_PASSWORD\'])"',
                env={"SCORING_PASSWORD": password}
            )
            task = execute_command.run(job)
            assert task['errored_out'] is False, f"Failed for password: {password}"
            assert task['output'] == password, f"Mismatch for password: {password!r}, got: {task['output']!r}"

    def test_no_env_vars(self):
        """Ensure jobs without env still work (backward compatibility)."""
        job = Job(environment_id="12345", command='python -c "print(\'OK\', end=\'\')"')
        task = execute_command.run(job)
        assert task['errored_out'] is False
        assert task['output'] == "OK"
