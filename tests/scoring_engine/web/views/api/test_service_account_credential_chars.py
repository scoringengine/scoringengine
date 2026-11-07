"""Service account credentials must be stored verbatim and may contain any
printable ASCII character.

Two separate defects are covered here:

1. ``update_service_account_info`` used to ``html.escape()`` the username and
   password before storing them.  Workers authenticate to the scored service
   with exactly these bytes, so escaping would mean the engine logs in with a
   different password than the one the blue team set -- the check fails and the
   team loses points for a service that is actually up.

2. The input validation regex rejected most password punctuation, so the web
   editor could not express credentials that ``competition.yaml`` provisioning
   (``competition.py``, which validates nothing) accepts happily.

The end-to-end assertion is ``test_password_reaches_command_verbatim``: it is
the one that would actually catch a regression in scoring behaviour, because it
follows the credential all the way into the command string the worker runs.
"""


import pytest

from scoring_engine.db import db
from scoring_engine.models.account import Account
from scoring_engine.models.environment import Environment
from scoring_engine.models.property import Property
from scoring_engine.models.service import Service
from scoring_engine.web.views.api.service import is_valid_user_input

# Characters that html.escape() rewrites.  Every one of these was previously
# rejected by validation, which is why the escaping bug was latent rather than
# live -- but the rejection was itself the user-facing problem.
ESCAPE_SENSITIVE = ["P@ss&word", "a<b>c", 'quote"inside', "apos'trophe", "&<>\"'"]

# Punctuation common in generated passwords that the old regex refused.
SHELL_SENSITIVE = ["dollar$var", "back`tick`", "pipe|sym", "semi;colon", "star*glob", "tilde~"]


class TestCredentialCharacterSet:
    """The validator itself, independent of HTTP plumbing."""

    @pytest.mark.parametrize("value", ESCAPE_SENSITIVE + SHELL_SENSITIVE)
    def test_printable_ascii_is_accepted(self, value):
        assert is_valid_user_input(value, False, False) is True

    @pytest.mark.parametrize("value", ["tab\there", "newline\nhere", "null\x00byte", "bell\x07"])
    def test_control_characters_are_rejected(self, value):
        assert is_valid_user_input(value, False, False) is False

    @pytest.mark.parametrize("value", ["café", "日本語", "emoji😀"])
    def test_non_ascii_is_rejected(self, value):
        assert is_valid_user_input(value, False, False) is False

    @pytest.mark.parametrize("value", [" leading", "trailing "])
    def test_edge_whitespace_is_rejected(self, value):
        assert is_valid_user_input(value, False, False) is False

    def test_interior_space_is_allowed(self):
        assert is_valid_user_input("two words", False, False) is True

    def test_hostname_validation_is_unchanged(self):
        """Widening applies only to credentials -- host stays strict."""
        assert is_valid_user_input("host.example.com", True, False) is True
        assert is_valid_user_input("host;rm -rf /", True, False) is False
        assert is_valid_user_input("host$(whoami)", True, False) is False

    def test_port_validation_is_unchanged(self):
        assert is_valid_user_input("443", False, True) is True
        assert is_valid_user_input("443;x", False, True) is False


class TestAccountCredentialsStoredVerbatim:
    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session, blue_login):
        self.client, self.teams = blue_login
        self.service = Service(
            name="TestSSH",
            check_name="SSHCheck",
            host="10.0.0.1",
            port=22,
            team=self.teams["blue_team"],
        )
        db.session.add(self.service)
        db.session.flush()
        self.account = Account(username="admin", password="secret", service=self.service)
        db.session.add(self.account)
        db.session.commit()

    def _update(self, field, value):
        return self.client.post(
            "/api/service/update_account",
            data={"pk": self.account.id, "name": field, "value": value},
        )

    @pytest.mark.parametrize("value", ESCAPE_SENSITIVE + SHELL_SENSITIVE)
    def test_password_round_trips_unmodified(self, value):
        resp = self._update("password", value)
        assert resp.json.get("status") == "Updated Account Information"
        db.session.refresh(self.account)
        # The exact bytes, not an HTML-escaped approximation of them.
        assert self.account.password == value

    @pytest.mark.parametrize("value", ESCAPE_SENSITIVE + SHELL_SENSITIVE)
    def test_username_round_trips_unmodified(self, value):
        resp = self._update("username", value)
        assert resp.json.get("status") == "Updated Account Information"
        db.session.refresh(self.account)
        assert self.account.username == value

    def test_ampersand_password_is_not_stored_as_entity(self):
        """Regression guard for the specific html.escape() defect."""
        self._update("password", "P@ss&word")
        db.session.refresh(self.account)
        assert self.account.password == "P@ss&word"
        assert "&amp;" not in self.account.password

    def test_control_character_still_rejected_over_http(self):
        resp = self._update("password", "bad\x00value")
        assert "error" in resp.json
        db.session.refresh(self.account)
        assert self.account.password == "secret"

    def test_rendered_page_escapes_the_credential(self):
        """Storing verbatim must not mean rendering raw."""
        self._update("password", '"><script>alert(1)</script>')
        resp = self.client.get(f"/service/{self.service.id}")
        body = resp.data.decode()
        assert "<script>alert(1)</script>" not in body
        assert "&lt;script&gt;" in body or "&amp;lt;script" in body


class TestCredentialReachesCommandVerbatim:
    """The property that actually protects scoring correctness."""

    @pytest.fixture(autouse=True)
    def setup(self, db_session, three_teams):
        self.service = Service(
            name="TestSSH",
            check_name="SSHCheck",
            host="10.0.0.1",
            port=22,
            team=three_teams["blue_team"],
        )
        db.session.add(self.service)
        db.session.flush()
        self.environment = Environment(service=self.service, matching_content="SUCCESS")
        db.session.add(self.environment)
        db.session.add(Property(name="commands", value="id", environment=self.environment))
        db.session.commit()

    @pytest.mark.parametrize("password", ["P@ss&word", "dollar$var", "back`tick`", "two words", "semi;colon"])
    def test_password_reaches_command_verbatim(self, password):
        """A credential with shell metacharacters must arrive intact as one argv entry.

        The password is passed via an environment variable (basic_check.Secret),
        so the command string only holds a reference. Run the command through a
        real shell, with the check binary swapped for printf, and confirm the
        argument the program receives is byte-for-byte the original password.
        """
        import os
        import subprocess

        from scoring_engine.checks.ssh import SSHCheck
        from scoring_engine.engine.basic_check import CHECKS_BIN_PATH

        account = Account(username="admin", password=password, service=self.service)
        db.session.add(account)
        db.session.commit()

        check = SSHCheck(self.environment)
        command = check.command()
        assert password not in command
        printf_cmd = command.replace(CHECKS_BIN_PATH + "/ssh_check", "printf '%s\\n'")
        out = subprocess.run(
            printf_cmd, shell=True, capture_output=True, text=True, env=dict(os.environ, **check.command_env)
        ).stdout
        # argv: host port username password commands show_command
        assert out.split("\n")[3] == password
