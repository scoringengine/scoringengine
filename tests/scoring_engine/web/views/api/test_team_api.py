"""Tests for Team API endpoints."""

import pytest

from scoring_engine.db import db
from scoring_engine.models.account import Account
from scoring_engine.models.check import Check
from scoring_engine.models.environment import Environment
from scoring_engine.models.property import Property
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.team import Team
from scoring_engine.web.views.api.team import calculate_ranks


class TestCalculateRanks:
    def test_normal_scores(self):
        scores = {1: 100, 2: 90, 3: 80}
        ranks = calculate_ranks(scores)
        assert ranks == {1: 1, 2: 2, 3: 3}

    def test_ties(self):
        scores = {1: 100, 2: 90, 3: 90, 4: 80}
        ranks = calculate_ranks(scores)
        assert ranks == {1: 1, 2: 2, 3: 2, 4: 4}

    def test_all_tied(self):
        scores = {1: 50, 2: 50, 3: 50}
        ranks = calculate_ranks(scores)
        assert ranks == {1: 1, 2: 1, 3: 1}

    def test_empty_dict(self):
        assert calculate_ranks({}) == {}

    def test_single_entry(self):
        scores = {1: 100}
        ranks = calculate_ranks(scores)
        assert ranks == {1: 1}


class TestTeamStatsAPI:
    @pytest.fixture(autouse=True)
    def setup(self, test_client, three_teams):
        self.client = test_client
        self.white_team = three_teams["white_team"]
        self.blue_team = three_teams["blue_team"]
        self.red_team = three_teams["red_team"]
        self.white_user = three_teams["white_user"]
        self.blue_user = three_teams["blue_user"]
        self.red_user = three_teams["red_user"]

    def login(self, username, password="testpass"):
        return self.client.post("/login", data={"username": username, "password": password}, follow_redirects=True)

    def test_requires_auth(self):
        resp = self.client.get(f"/api/team/{self.blue_team.id}/stats")
        assert resp.status_code == 302

    def test_blue_team_own_stats(self):
        self.login(self.blue_user.username)
        resp = self.client.get(f"/api/team/{self.blue_team.id}/stats")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "place" in data
        assert "current_score" in data

    def test_blue_team_cannot_see_other_team(self):
        self.login(self.blue_user.username)
        resp = self.client.get(f"/api/team/{self.red_team.id}/stats")
        assert resp.status_code == 403

    def test_white_team_denied(self):
        self.login(self.white_user.username)
        resp = self.client.get(f"/api/team/{self.blue_team.id}/stats")
        assert resp.status_code == 403

    def test_red_team_denied(self):
        self.login(self.red_user.username)
        resp = self.client.get(f"/api/team/{self.blue_team.id}/stats")
        assert resp.status_code == 403

    def test_nonexistent_team(self):
        self.login(self.blue_user.username)
        resp = self.client.get("/api/team/99999/stats")
        assert resp.status_code == 403


class TestTeamServicesAPI:
    @pytest.fixture(autouse=True)
    def setup(self, test_client, three_teams):
        self.client = test_client
        self.white_team = three_teams["white_team"]
        self.blue_team = three_teams["blue_team"]
        self.red_team = three_teams["red_team"]
        self.white_user = three_teams["white_user"]
        self.blue_user = three_teams["blue_user"]
        self.red_user = three_teams["red_user"]

    def login(self, username, password="testpass"):
        return self.client.post("/login", data={"username": username, "password": password}, follow_redirects=True)

    def _create_service(self, team, name="TestSSH", host="10.0.0.1", port=22, check_name="SSHCheck"):
        service = Service(name=name, team=team, check_name=check_name, host=host, port=port)
        db.session.add(service)
        db.session.flush()
        env = Environment(service=service, matching_content=".*")
        db.session.add(env)
        db.session.flush()
        prop = Property(name="username", value="root", environment=env)
        db.session.add(prop)
        account = Account(username="root", password="toor", service=service)
        db.session.add(account)
        db.session.commit()
        return service

    def test_requires_auth(self):
        resp = self.client.get(f"/api/team/{self.blue_team.id}/services")
        assert resp.status_code == 302

    def test_blue_team_cannot_see_other_team(self):
        self.login(self.blue_user.username)
        resp = self.client.get(f"/api/team/{self.red_team.id}/services")
        assert resp.status_code == 403

    def test_empty_services(self):
        self.login(self.blue_user.username)
        resp = self.client.get(f"/api/team/{self.blue_team.id}/services")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"] == []

    def test_service_with_no_checks(self):
        self._create_service(self.blue_team)
        self.login(self.blue_user.username)
        resp = self.client.get(f"/api/team/{self.blue_team.id}/services")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert len(data) == 1
        assert data[0]["check"] == "Undetermined"
        assert data[0]["service_name"] == "TestSSH"
        assert data[0]["host"] == "10.0.0.1"
        assert data[0]["port"] == "22"

    def test_service_with_passing_check(self):
        service = self._create_service(self.blue_team)
        round_obj = Round(number=1)
        db.session.add(round_obj)
        db.session.flush()
        check = Check(service=service, round=round_obj, result=True, output="OK")
        db.session.add(check)
        db.session.commit()

        self.login(self.blue_user.username)
        resp = self.client.get(f"/api/team/{self.blue_team.id}/services")
        data = resp.get_json()["data"]
        assert data[0]["check"] == "UP"

    def test_service_with_failing_check(self):
        service = self._create_service(self.blue_team)
        round_obj = Round(number=1)
        db.session.add(round_obj)
        db.session.flush()
        check = Check(service=service, round=round_obj, result=False, output="FAIL")
        db.session.add(check)
        db.session.commit()

        self.login(self.blue_user.username)
        resp = self.client.get(f"/api/team/{self.blue_team.id}/services")
        data = resp.get_json()["data"]
        assert data[0]["check"] == "DOWN"

    def test_service_response_fields(self):
        service = self._create_service(self.blue_team, name="SSH", host="10.0.0.5", port=2222)
        round_obj = Round(number=1)
        db.session.add(round_obj)
        db.session.flush()
        check = Check(service=service, round=round_obj, result=True, output="OK")
        db.session.add(check)
        db.session.commit()

        self.login(self.blue_user.username)
        resp = self.client.get(f"/api/team/{self.blue_team.id}/services")
        data = resp.get_json()["data"][0]
        assert data["service_id"] == str(service.id)
        assert data["service_name"] == "SSH"
        assert data["host"] == "10.0.0.5"
        assert data["port"] == "2222"
        assert "rank" in data
        assert "score_earned" in data
        assert "max_score" in data
        assert "percent_earned" in data
        assert "pts_per_check" in data
        assert "last_ten_checks" in data

    def test_multiple_services(self):
        self._create_service(self.blue_team, name="SSH", host="10.0.0.1", port=22)
        self._create_service(self.blue_team, name="HTTP", host="10.0.0.1", port=80, check_name="HTTPCheck")

        self.login(self.blue_user.username)
        resp = self.client.get(f"/api/team/{self.blue_team.id}/services")
        data = resp.get_json()["data"]
        assert len(data) == 2


class TestTeamServicesStatusAPI:
    @pytest.fixture(autouse=True)
    def setup(self, test_client, three_teams):
        self.client = test_client
        self.blue_team = three_teams["blue_team"]
        self.red_team = three_teams["red_team"]
        self.blue_user = three_teams["blue_user"]

    def login(self, username, password="testpass"):
        return self.client.post("/login", data={"username": username, "password": password}, follow_redirects=True)

    def test_requires_auth(self):
        resp = self.client.get(f"/api/team/{self.blue_team.id}/services/status")
        assert resp.status_code == 302

    def test_blue_team_cannot_see_other_team(self):
        self.login(self.blue_user.username)
        resp = self.client.get(f"/api/team/{self.red_team.id}/services/status")
        assert resp.status_code == 403

    def test_no_rounds_returns_empty(self):
        self.login(self.blue_user.username)
        resp = self.client.get(f"/api/team/{self.blue_team.id}/services/status")
        assert resp.status_code == 200

    def test_returns_service_status(self):
        service = Service(name="SSH", team=self.blue_team, check_name="SSHCheck", host="10.0.0.1", port=22)
        db.session.add(service)
        db.session.flush()
        env = Environment(service=service, matching_content=".*")
        db.session.add(env)
        round_obj = Round(number=1)
        db.session.add(round_obj)
        db.session.flush()
        check = Check(service=service, round=round_obj, result=True, output="OK")
        db.session.add(check)
        db.session.commit()

        self.login(self.blue_user.username)
        resp = self.client.get(f"/api/team/{self.blue_team.id}/services/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "SSH" in data
        assert data["SSH"]["result"] == "True"
        assert data["SSH"]["check_name"] == "SSHCheck"
        assert data["SSH"]["host"] == "10.0.0.1"

    def test_returns_latest_round_only(self):
        service = Service(name="SSH", team=self.blue_team, check_name="SSHCheck", host="10.0.0.1", port=22)
        db.session.add(service)
        db.session.flush()
        env = Environment(service=service, matching_content=".*")
        db.session.add(env)

        round1 = Round(number=1)
        round2 = Round(number=2)
        db.session.add_all([round1, round2])
        db.session.flush()

        check1 = Check(service=service, round=round1, result=False, output="FAIL")
        check2 = Check(service=service, round=round2, result=True, output="OK")
        db.session.add_all([check1, check2])
        db.session.commit()

        self.login(self.blue_user.username)
        resp = self.client.get(f"/api/team/{self.blue_team.id}/services/status")
        data = resp.get_json()
        # Should show round 2 (latest) result
        assert data["SSH"]["result"] == "True"
