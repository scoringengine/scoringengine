from unittest import mock

import scoring_engine.engine.execute_command as ec
from scoring_engine.db import db
from scoring_engine.engine.basic_check import BasicCheck, Secret
from scoring_engine.engine.execute_command import execute_command
from scoring_engine.engine.job import Job
from scoring_engine.models.account import Account
from scoring_engine.models.environment import Environment
from scoring_engine.models.service import Service

HOSTILE = "p a$(touch /tmp/se_pwned)`id`;'\"\\\n$HOME end"


class EchoCheck(BasicCheck):
    CMD = "printf '%s|%s' {0} {1}"

    def command_format(self, properties):
        account = self.get_random_account()
        return (account.username, self.secret(account.password))


def _check(password):
    service = Service(name="svc", check_name="EchoCheck", host="127.0.0.1", port=1)
    environment = Environment(service=service, matching_content=".")
    db.session.add_all([service, environment, Account(username="alice", password=password, service=service)])
    db.session.commit()
    return EchoCheck(environment)


class TestCheckSecrets:
    def test_secret_rendered_as_env_reference(self):
        check = _check("hunter2")
        assert check.command() == "printf '%s|%s' alice \"${SE_SECRET_0}\""
        assert check.command_env == {"SE_SECRET_0": "hunter2"}

    def test_secret_repr_hides_value(self):
        assert "hunter2" not in repr(Secret("hunter2"))

    def test_hostile_password_round_trips_without_executing(self, tmp_path):
        check = _check(HOSTILE)
        job = Job(environment_id=1, command=check.command(), env=check.command_env)
        assert "touch" not in job["command"]
        with mock.patch.object(ec, "logger") as mock_logger:
            mock_logger.propagate = False
            result = execute_command(job)
        assert result["output"] == "alice|" + HOSTILE
        assert "env" not in result

    def test_job_without_env_still_runs(self):
        result = execute_command(Job(environment_id=1, command="echo plain"))
        assert result["output"] == "plain\n"
