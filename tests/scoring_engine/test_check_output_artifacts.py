"""Tests for check output artifact storage: config, engine writing, and API retrieval."""

import os
import shutil

import pytest

from scoring_engine.config import config
from scoring_engine.config_loader import ConfigLoader
from scoring_engine.db import db
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team


class TestCheckOutputFolderConfig:
    def test_check_output_folder_from_config(self):
        cfg = ConfigLoader(location="../tests/scoring_engine/engine.conf.inc")
        assert cfg.check_output_folder == "/tmp/test_check_outputs"

    def test_check_output_folder_default(self):
        cfg = ConfigLoader(location="../tests/scoring_engine/engine.conf.inc")
        assert cfg.parse_sources("check_output_folder_missing", "/var/check_outputs") == "/var/check_outputs"

    def test_check_output_folder_env_override(self):
        os.environ["SCORINGENGINE_CHECK_OUTPUT_FOLDER"] = "/custom/path"
        try:
            cfg = ConfigLoader(location="../tests/scoring_engine/engine.conf.inc")
            assert cfg.check_output_folder == "/custom/path"
        finally:
            del os.environ["SCORINGENGINE_CHECK_OUTPUT_FOLDER"]


class TestCheckOutputAPI:
    @pytest.fixture(autouse=True)
    def setup(self, test_client, three_teams):
        self.client = test_client
        self.teams = three_teams
        # Use the path that the app's config instance actually reads
        self.output_dir = config.check_output_folder

    def login(self, username, password="testpass"):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    def _create_check_with_output(self, team, output_content):
        """Create a check in the DB and write its full output file."""
        service = Service(name="TestService", check_name="ICMP IPv4 Check", host="1.2.3.4", team=team)
        round_obj = Round(number=1)
        db.session.add_all([service, round_obj])
        db.session.flush()

        check = Check(service=service, round=round_obj)
        check.finished(result=True, reason="Check Passed", output=output_content[:5000], command="test_cmd")
        db.session.add(check)
        db.session.commit()

        # Write the full output file to the configured output folder
        file_dir = os.path.join(self.output_dir, team.name, service.name)
        os.makedirs(file_dir, exist_ok=True)
        output_file = os.path.join(file_dir, f"round_{round_obj.number}.txt")
        with open(output_file, "w") as f:
            f.write(output_content)

        return check

    def _cleanup_output_dir(self):
        """Remove test output files."""
        if os.path.isdir(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_requires_auth(self):
        resp = self.client.get("/api/admin/check/1/full_output")
        assert resp.status_code == 302

    def test_requires_white_team(self):
        team = self.teams["blue_team"]
        check = self._create_check_with_output(team, "some output")
        try:
            self.login("blueuser")
            resp = self.client.get(f"/api/admin/check/{check.id}/full_output")
            assert resp.status_code == 403
        finally:
            self._cleanup_output_dir()

    def test_returns_full_output(self):
        team = self.teams["blue_team"]
        full_output = "A" * 10000
        check = self._create_check_with_output(team, full_output)
        try:
            self.login("whiteuser")
            resp = self.client.get(f"/api/admin/check/{check.id}/full_output")
            assert resp.status_code == 200, resp.data
            assert resp.content_type.startswith("text/plain")
            assert len(resp.data.decode()) == 10000
        finally:
            self._cleanup_output_dir()

    def test_check_not_found(self):
        self.login("whiteuser")
        resp = self.client.get("/api/admin/check/99999/full_output")
        assert resp.status_code == 404

    def test_file_not_found(self):
        team = self.teams["blue_team"]
        service = Service(name="TestService", check_name="ICMP IPv4 Check", host="1.2.3.4", team=team)
        round_obj = Round(number=99)
        db.session.add_all([service, round_obj])
        db.session.flush()
        check = Check(service=service, round=round_obj)
        check.finished(result=True, reason="Check Passed", output="preview", command="cmd")
        db.session.add(check)
        db.session.commit()

        self.login("whiteuser")
        resp = self.client.get(f"/api/admin/check/{check.id}/full_output")
        assert resp.status_code == 404
        assert resp.json["error"] == "Full output file not found"
