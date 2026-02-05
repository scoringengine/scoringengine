import json
from datetime import datetime, timedelta, timezone

from scoring_engine.cache import cache
from scoring_engine.models.check import Check
from scoring_engine.models.environment import Environment
from scoring_engine.models.inject import Inject, Template
from scoring_engine.models.round import Round
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team
from scoring_engine.web.views.api.service import is_valid_user_input
from tests.scoring_engine.web.web_test import WebTest


class TestAPI(WebTest):

    def setup_method(self):
        super(TestAPI, self).setup_method()
        self.create_default_user()

    def set_setting(self, name, value):
        """Helper to update a setting value in tests."""
        from scoring_engine.db import db
        Setting.clear_cache()  # Clear cache first to ensure fresh query
        setting = db.session.query(Setting).filter(Setting.name == name).first()
        if setting:
            # Convert string "True"/"False" to bool for boolean settings
            if value == "True":
                setting.value = True
            elif value == "False":
                setting.value = False
            else:
                setting.value = value
            db.session.commit()
        # Clear both Setting model cache and Flask memoize cache
        Setting.clear_cache()
        cache.clear()

    def test_auth_required_admin_get_round_progress(self):
        self.verify_auth_required("/api/admin/get_round_progress")

    def test_auth_required_admin_get_teams(self):
        self.verify_auth_required("/api/admin/get_teams")

    def test_auth_required_admin_update_password(self):
        self.verify_auth_required_post("/api/admin/update_password")

    def test_auth_required_admin_add_user(self):
        self.verify_auth_required_post("/api/admin/add_user")

    def test_auth_required_profile_update_password(self):
        self.verify_auth_required_post("/api/profile/update_password")

    def test_auth_required_service_get_checks_id(self):
        self.verify_auth_required("/api/service/1/checks")

    """
    def test_api_scoreboard_get_bar_data(self):
        resp = self.client.get('api/scoreboard/get_bar_data')
        assert resp.status_code == 200

    def test_api_scoreboard_get_line_data(self):
        resp = self.client.get('/api/scoreboard/get_line_data')
        assert resp.status_code == 200
    """

    def test_overview_data_no_teams(self):
        overview_data = self.client.get("/api/overview/data")
        assert json.loads(overview_data.data.decode("utf8")) == {}

    def test_overview_data(self):
        # create 1 white team, 1 red team, 5 blue teams, 3 services per team, 5 checks per service
        # White Team
        self.session.add(Team(name="whiteteam", color="White"))
        # Red Team
        self.session.add(Team(name="redteam", color="Red"))
        self.session.commit()
        teams = []
        last_check_results = {
            "team1": {
                "FTP": True,
                "DNS": True,
                "ICMP": True,
            },
            "team2": {
                "FTP": False,
                "DNS": True,
                "ICMP": True,
            },
            "team3": {
                "FTP": False,
                "DNS": True,
                "ICMP": False,
            },
            "team4": {
                "FTP": True,
                "DNS": False,
                "ICMP": False,
            },
            "team5": {
                "FTP": False,
                "DNS": False,
                "ICMP": False,
            },
        }
        for team_num in range(1, 6):
            team = Team(name="team" + str(team_num), color="Blue")
            icmp_service = Service(
                name="ICMP", team=team, check_name="ICMP IPv4 Check", host="127.0.0.1"
            )
            dns_service = Service(
                name="DNS", team=team, check_name="DNSCheck", host="8.8.8.8", port=53
            )
            ftp_service = Service(
                name="FTP", team=team, check_name="FTPCheck", host="1.2.3.4", port=21
            )
            self.session.add(icmp_service)
            self.session.add(dns_service)
            self.session.add(ftp_service)
            # 5 rounds of checks
            round_1 = Round(number=1)
            icmp_check_1 = Check(
                round=round_1,
                service=icmp_service,
                result=True,
                output="example_output",
            )
            dns_check_1 = Check(
                round=round_1,
                service=dns_service,
                result=False,
                output="example_output",
            )
            ftp_check_1 = Check(
                round=round_1, service=ftp_service, result=True, output="example_output"
            )
            self.session.add(round_1)
            self.session.add(icmp_check_1)
            self.session.add(dns_check_1)
            self.session.add(ftp_check_1)

            round_2 = Round(number=2)
            icmp_check_2 = Check(
                round=round_2,
                service=icmp_service,
                result=True,
                output="example_output",
            )
            dns_check_2 = Check(
                round=round_2, service=dns_service, result=True, output="example_output"
            )
            ftp_check_2 = Check(
                round=round_2, service=ftp_service, result=True, output="example_output"
            )
            self.session.add(round_2)
            self.session.add(icmp_check_2)
            self.session.add(dns_check_2)
            self.session.add(ftp_check_2)

            round_3 = Round(number=3)
            icmp_check_3 = Check(
                round=round_3,
                service=icmp_service,
                result=True,
                output="example_output",
            )
            dns_check_3 = Check(
                round=round_3,
                service=dns_service,
                result=False,
                output="example_output",
            )
            ftp_check_3 = Check(
                round=round_3, service=ftp_service, result=True, output="example_output"
            )
            self.session.add(round_3)
            self.session.add(icmp_check_3)
            self.session.add(dns_check_3)
            self.session.add(ftp_check_3)

            round_4 = Round(number=4)
            icmp_check_4 = Check(
                round=round_4,
                service=icmp_service,
                result=False,
                output="example_output",
            )
            dns_check_4 = Check(
                round=round_4,
                service=dns_service,
                result=False,
                output="example_output",
            )
            ftp_check_4 = Check(
                round=round_4,
                service=ftp_service,
                result=False,
                output="example_output",
            )
            self.session.add(round_4)
            self.session.add(icmp_check_4)
            self.session.add(dns_check_4)
            self.session.add(ftp_check_4)

            round_5 = Round(number=5)
            icmp_check_5 = Check(
                round=round_5,
                service=icmp_service,
                result=last_check_results[team.name]["ICMP"],
                output="example_output",
            )
            dns_check_5 = Check(
                round=round_5,
                service=dns_service,
                result=last_check_results[team.name]["DNS"],
                output="example_output",
            )
            ftp_check_5 = Check(
                round=round_5,
                service=ftp_service,
                result=last_check_results[team.name]["FTP"],
                output="example_output",
            )
            self.session.add(round_5)
            self.session.add(icmp_check_5)
            self.session.add(dns_check_5)
            self.session.add(ftp_check_5)

            self.session.add(team)
            self.session.commit()
            teams.append(team)

        overview_data = self.client.get("/api/overview/data")
        overview_dict = json.loads(overview_data.data.decode("utf8"))
        expected_dict = {
            "team1": {
                "FTP": {"passing": True, "host": "1.2.3.4", "port": 21},
                "DNS": {"passing": True, "host": "8.8.8.8", "port": 53},
                "ICMP": {"passing": True, "host": "127.0.0.1", "port": 0},
            },
            "team2": {
                "FTP": {"passing": False, "host": "1.2.3.4", "port": 21},
                "DNS": {"passing": True, "host": "8.8.8.8", "port": 53},
                "ICMP": {"passing": True, "host": "127.0.0.1", "port": 0},
            },
            "team3": {
                "FTP": {"passing": False, "host": "1.2.3.4", "port": 21},
                "DNS": {"passing": True, "host": "8.8.8.8", "port": 53},
                "ICMP": {"passing": False, "host": "127.0.0.1", "port": 0},
            },
            "team4": {
                "FTP": {"passing": True, "host": "1.2.3.4", "port": 21},
                "DNS": {"passing": False, "host": "8.8.8.8", "port": 53},
                "ICMP": {"passing": False, "host": "127.0.0.1", "port": 0},
            },
            "team5": {
                "FTP": {"passing": False, "host": "1.2.3.4", "port": 21},
                "DNS": {"passing": False, "host": "8.8.8.8", "port": 53},
                "ICMP": {"passing": False, "host": "127.0.0.1", "port": 0},
            },
        }
        assert sorted(overview_dict.items()) == sorted(expected_dict.items())

    def test_get_engine_stats(self):
        resp = self.auth_and_get_path("/api/admin/get_engine_stats")
        resp_json = json.loads(resp.data.decode("ascii"))
        assert resp_json == {
            "num_passed_checks": 0,
            "total_checks": 0,
            "round_number": 0,
            "num_failed_checks": 0,
        }

    def test_admin_update_environment(self):
        self.login("testuser", "testpass")
        team = self.session.query(Team).first()
        service = Service(
            name="Example", check_name="ICMP IPv4 Check", host="1.2.3.4", team=team
        )
        env = Environment(service=service, matching_content="old")
        self.session.add_all([service, env])
        self.session.commit()
        resp = self.client.post(
            "/api/admin/update_environment_info",
            data={"pk": env.id, "name": "matching_content", "value": "new"},
        )
        assert resp.json == {"status": "Updated Environment Information"}
        self.session.refresh(env)
        assert env.matching_content == "new"

    def test_service_update_host_invalid_input(self):
        self.login("testuser", "testpass")
        team = self.session.query(Team).first()
        service = Service(
            name="Example", check_name="ICMP IPv4 Check", host="1.2.3.4", team=team
        )
        self.session.add(service)
        self.session.commit()
        resp = self.client.post(
            "/api/service/update_host",
            data={"pk": service.id, "name": "host", "value": "bad host"},
        )
        assert resp.json == {"error": "Invalid input characters detected"}

    def test_is_valid_user_input(self):
        assert is_valid_user_input("abc123", True, False)
        assert not is_valid_user_input("bad host", True, False)
        assert is_valid_user_input("12345", False, True)
        assert not is_valid_user_input("12a", False, True)
        assert is_valid_user_input("hello world", False, False)
        assert not is_valid_user_input(" leading", False, False)

    def test_inject_add_comment_no_comment(self):
        self.login("testuser", "testpass")
        team = self.session.query(Team).first()
        template = Template(
            title="t",
            scenario="s",
            deliverable="d",
            score=10,
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        inject = Inject(team=team, template=template)
        self.session.add_all([template, inject])
        self.session.commit()
        resp = self.client.post(f"/api/inject/{inject.id}/comment", json={})
        assert resp.status_code == 400
        assert resp.json == {"status": "No comment"}

    def test_api_scoreboard_get_bar_data_no_sla(self):
        """Test scoreboard bar data without SLA penalties."""

        # Ensure SLA is disabled
        self.set_setting("sla_enabled", "False")

        # Create teams and services with checks
        team1 = Team(name="Team Alpha", color="Blue")
        team2 = Team(name="Team Beta", color="Blue")
        self.session.add_all([team1, team2])
        self.session.commit()

        service1 = Service(
            name="HTTP",
            team=team1,
            check_name="HTTPCheck",
            host="1.2.3.4",
            port=80,
            points=100,
        )
        service2 = Service(
            name="SSH",
            team=team2,
            check_name="SSHCheck",
            host="1.2.3.5",
            port=22,
            points=100,
        )
        self.session.add_all([service1, service2])

        # Add passing checks
        round1 = Round(number=1)
        self.session.add(round1)
        check1 = Check(service=service1, round=round1, result=True, output="OK")
        check2 = Check(service=service2, round=round1, result=True, output="OK")
        self.session.add_all([check1, check2])
        self.session.commit()

        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = resp.json

        assert "labels" in data
        assert "service_scores" in data
        assert "sla_penalties" in data
        assert "adjusted_scores" in data
        assert "sla_enabled" in data
        assert data["sla_enabled"] is False
        # Without SLA, penalties should be 0
        assert all(p == "0" for p in data["sla_penalties"])

    def test_api_scoreboard_get_bar_data_with_sla_penalties(self):
        """Test scoreboard bar data with SLA penalties enabled."""

        # Enable SLA with threshold 3
        self.set_setting("sla_enabled", "True")
        self.set_setting("sla_penalty_threshold", "3")
        self.set_setting("sla_penalty_percent", "10")
        self.set_setting("sla_penalty_max_percent", "50")
        self.set_setting("sla_penalty_mode", "additive")
        self.set_setting("sla_allow_negative", "False")

        # Create team with service
        team1 = Team(name="Team Gamma", color="Blue")
        self.session.add(team1)
        self.session.commit()

        service1 = Service(
            name="DNS",
            team=team1,
            check_name="DNSCheck",
            host="8.8.8.8",
            port=53,
            points=100,
        )
        self.session.add(service1)

        # Create 6 rounds - first 2 pass, then 4 consecutive failures
        for i in range(1, 7):
            round_obj = Round(number=i)
            self.session.add(round_obj)
            self.session.flush()  # Ensure round_id is assigned before creating checks
            # First 2 rounds pass, rounds 3-6 fail (4 consecutive failures)
            result = i <= 2
            check = Check(
                service=service1, round=round_obj, result=result, output="test", completed=True
            )
            self.session.add(check)
        self.session.commit()

        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = resp.json

        assert data["sla_enabled"] is True
        assert "Team Gamma" in data["labels"]

        # Should have penalties since 4 consecutive failures > threshold 3
        team_idx = data["labels"].index("Team Gamma")
        penalty = int(data["sla_penalties"][team_idx])
        assert penalty > 0, "Should have SLA penalty for consecutive failures"

        # Adjusted score should be less than base score
        base_score = int(data["service_scores"][team_idx])
        adjusted_score = int(data["adjusted_scores"][team_idx])
        assert (
            adjusted_score < base_score
        ), "Adjusted score should be reduced by penalty"

    def test_api_scoreboard_multiple_teams_with_penalties(self):
        """Test scoreboard with multiple teams having different penalty levels."""

        self.set_setting("sla_enabled", "True")
        self.set_setting("sla_penalty_threshold", "2")
        self.set_setting("sla_penalty_percent", "20")
        self.set_setting("sla_penalty_max_percent", "100")
        self.set_setting("sla_penalty_mode", "additive")
        self.set_setting("sla_allow_negative", "False")

        # Team 1: All passes (no penalty)
        team1 = Team(name="NoFailures", color="Blue")
        # Team 2: Some failures but not consecutive enough
        team2 = Team(name="FewFailures", color="Blue")
        # Team 3: Many consecutive failures (high penalty)
        team3 = Team(name="ManyFailures", color="Blue")
        self.session.add_all([team1, team2, team3])
        self.session.commit()

        service1 = Service(
            name="Web",
            team=team1,
            check_name="HTTPCheck",
            host="1.1.1.1",
            port=80,
            points=100,
        )
        service2 = Service(
            name="Web",
            team=team2,
            check_name="HTTPCheck",
            host="2.2.2.2",
            port=80,
            points=100,
        )
        service3 = Service(
            name="Web",
            team=team3,
            check_name="HTTPCheck",
            host="3.3.3.3",
            port=80,
            points=100,
        )
        self.session.add_all([service1, service2, service3])

        # 5 rounds
        for i in range(1, 6):
            round_obj = Round(number=i)
            self.session.add(round_obj)
            self.session.flush()  # Ensure round_id is assigned before creating checks
            # Team 1: All pass
            check1 = Check(service_id=service1.id, round_id=round_obj.id, result=True, output="ok", completed=True)
            # Team 2: Pass, pass, fail, pass, fail (no consecutive >= threshold)
            check2_result = i not in [3, 5]
            check2 = Check(
                service_id=service2.id, round_id=round_obj.id, result=check2_result, output="ok", completed=True
            )
            # Team 3: Pass, fail, fail, fail, fail (4 consecutive failures)
            check3_result = i == 1
            check3 = Check(
                service_id=service3.id, round_id=round_obj.id, result=check3_result, output="ok", completed=True
            )
            self.session.add_all([check1, check2, check3])
        self.session.commit()

        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = resp.json

        # Find team indices
        idx1 = data["labels"].index("NoFailures")
        idx2 = data["labels"].index("FewFailures")
        idx3 = data["labels"].index("ManyFailures")

        # Team 1 should have no penalty
        assert int(data["sla_penalties"][idx1]) == 0

        # Team 2 should have no penalty (failures not consecutive enough)
        assert int(data["sla_penalties"][idx2]) == 0

        # Team 3 should have a penalty (4 consecutive failures > threshold 2)
        assert int(data["sla_penalties"][idx3]) > 0

    def test_api_sla_summary(self):
        """Test the SLA summary API endpoint."""

        self.login("testuser", "testpass")

        self.set_setting("sla_enabled", "True")
        self.set_setting("sla_penalty_threshold", "3")
        self.set_setting("sla_penalty_percent", "15")
        self.set_setting("sla_penalty_max_percent", "50")
        self.set_setting("sla_penalty_mode", "additive")
        self.set_setting("sla_allow_negative", "False")

        team = Team(name="SLA Test Team", color="Blue")
        self.session.add(team)
        self.session.commit()

        service = Service(
            name="FTP",
            team=team,
            check_name="FTPCheck",
            host="5.5.5.5",
            port=21,
            points=100,
        )
        self.session.add(service)

        # Create 5 rounds with 4 consecutive failures at end
        for i in range(1, 6):
            round_obj = Round(number=i)
            self.session.add(round_obj)
            self.session.flush()  # Ensure round_id is assigned before creating checks
            result = i == 1  # Only first round passes
            check = Check(
                service=service, round=round_obj, result=result, output="test", completed=True
            )
            self.session.add(check)
        self.session.commit()

        resp = self.client.get("/api/sla/summary")
        assert resp.status_code == 200
        data = resp.json

        assert "teams" in data
        assert len(data["teams"]) >= 1

        # Find our test team
        test_team_data = None
        for t in data["teams"]:
            if t["team_name"] == "SLA Test Team":
                test_team_data = t
                break

        assert test_team_data is not None
        assert "base_score" in test_team_data
        assert "total_penalties" in test_team_data
        assert "adjusted_score" in test_team_data
        assert "services_with_violations" in test_team_data

        # 4 consecutive failures > threshold 3, so should have penalty
        assert test_team_data["total_penalties"] > 0
        assert test_team_data["services_with_violations"] >= 1

    def test_api_sla_team_details(self):
        """Test the SLA team details API endpoint."""
        from scoring_engine.models.user import User

        self.set_setting("sla_enabled", "True")
        self.set_setting("sla_penalty_threshold", "2")
        self.set_setting("sla_penalty_percent", "10")
        self.set_setting("sla_penalty_max_percent", "50")
        self.set_setting("sla_penalty_mode", "additive")

        team = Team(name="Team Details Test", color="Blue")
        self.session.add(team)
        self.session.commit()

        # Create user on this team to view their own team's details
        user = User(username="teamuser", password="teampass", team=team)
        self.session.add(user)
        self.session.commit()

        service1 = Service(
            name="SSH",
            team=team,
            check_name="SSHCheck",
            host="6.6.6.6",
            port=22,
            points=100,
        )
        service2 = Service(
            name="HTTP",
            team=team,
            check_name="HTTPCheck",
            host="7.7.7.7",
            port=80,
            points=100,
        )
        self.session.add_all([service1, service2])

        # Service 1: 3 consecutive failures
        # Service 2: All passes
        for i in range(1, 4):
            round_obj = Round(number=i)
            self.session.add(round_obj)
            self.session.flush()  # Ensure round_id is assigned before creating checks
            check1 = Check(
                service_id=service1.id, round_id=round_obj.id, result=False, output="fail", completed=True
            )
            check2 = Check(service_id=service2.id, round_id=round_obj.id, result=True, output="ok", completed=True)
            self.session.add_all([check1, check2])
        self.session.commit()

        # Login as user on this team
        self.login("teamuser", "teampass")

        resp = self.client.get(f"/api/sla/team/{team.id}")
        assert resp.status_code == 200
        data = resp.json

        assert "team_id" in data
        assert "team_name" in data
        assert "services" in data
        assert data["team_name"] == "Team Details Test"

        # Should have 2 services
        assert len(data["services"]) == 2

        # Find SSH service (should have violations)
        ssh_service = None
        http_service = None
        for s in data["services"]:
            if s["service_name"] == "SSH":
                ssh_service = s
            elif s["service_name"] == "HTTP":
                http_service = s

        assert ssh_service is not None
        assert http_service is not None

        # SSH has 3 consecutive failures > threshold 2
        assert ssh_service["consecutive_failures"] == 3
        assert ssh_service["penalty_percent"] > 0

        # HTTP has all passes
        assert http_service["consecutive_failures"] == 0
        assert http_service["penalty_percent"] == 0

    def test_api_sla_dynamic_scoring_info(self):
        """Test the dynamic scoring info API endpoint."""

        self.login("testuser", "testpass")

        self.set_setting("dynamic_scoring_enabled", "True")
        self.set_setting("dynamic_scoring_early_rounds", "5")
        self.set_setting("dynamic_scoring_early_multiplier", "2.0")
        self.set_setting("dynamic_scoring_late_start_round", "20")
        self.set_setting("dynamic_scoring_late_multiplier", "0.5")

        # Create some rounds
        for i in range(1, 4):
            round_obj = Round(number=i)
            self.session.add(round_obj)
        self.session.commit()

        resp = self.client.get("/api/sla/dynamic-scoring")
        assert resp.status_code == 200
        data = resp.json

        assert data["enabled"] is True
        assert data["current_round"] == 3
        assert data["early_rounds"] == 5
        assert data["early_multiplier"] == 2.0
        assert data["late_start_round"] == 20
        assert data["late_multiplier"] == 0.5
        # Round 3 is in early phase (< 5)
        assert data["current_phase"] == "early"
        assert data["current_multiplier"] == 2.0

    def test_api_scoreboard_with_dynamic_scoring_multipliers(self):
        """Test that dynamic scoring multipliers are applied to scores."""

        # Enable dynamic scoring with 2x multiplier for early rounds
        self.set_setting("sla_enabled", "False")
        self.set_setting("dynamic_scoring_enabled", "True")
        self.set_setting("dynamic_scoring_early_rounds", "5")
        self.set_setting("dynamic_scoring_early_multiplier", "2.0")
        self.set_setting("dynamic_scoring_late_start_round", "50")
        self.set_setting("dynamic_scoring_late_multiplier", "0.5")

        # Create a team with a service
        team = Team(name="Dynamic Team", color="Blue")
        self.session.add(team)
        self.session.commit()

        service = Service(
            name="Web",
            team=team,
            check_name="HTTPCheck",
            host="10.10.10.10",
            port=80,
            points=100,
        )
        self.session.add(service)

        # Create 3 rounds (all in early phase), all checks pass
        # Without dynamic scoring: 3 * 100 = 300
        # With 2x early multiplier: 3 * 100 * 2 = 600
        for i in range(1, 4):
            round_obj = Round(number=i)
            self.session.add(round_obj)
            self.session.flush()  # Ensure round_id is assigned before creating checks
            check = Check(service=service, round=round_obj, result=True, output="ok", completed=True)
            self.session.add(check)
        self.session.commit()

        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = resp.json

        team_idx = data["labels"].index("Dynamic Team")
        score = int(data["service_scores"][team_idx])

        # With dynamic scoring enabled and 2x multiplier, score should be 600
        assert score == 600, f"Expected 600 with 2x multiplier, got {score}"

    def test_api_scoreboard_dynamic_scoring_late_phase(self):
        """Test dynamic scoring in late phase reduces scores."""

        self.set_setting("sla_enabled", "False")
        self.set_setting("dynamic_scoring_enabled", "True")
        self.set_setting("dynamic_scoring_early_rounds", "5")
        self.set_setting("dynamic_scoring_early_multiplier", "2.0")
        self.set_setting("dynamic_scoring_late_start_round", "10")
        self.set_setting("dynamic_scoring_late_multiplier", "0.5")

        team = Team(name="Late Phase Team", color="Blue")
        self.session.add(team)
        self.session.commit()

        service = Service(
            name="SSH",
            team=team,
            check_name="SSHCheck",
            host="11.11.11.11",
            port=22,
            points=100,
        )
        self.session.add(service)

        # Create rounds: 5 early (2x), 4 normal (1x), 3 late (0.5x)
        # Early: 5 * 100 * 2.0 = 1000
        # Normal (rounds 6-9): 4 * 100 * 1.0 = 400
        # Late (rounds 10-12): 3 * 100 * 0.5 = 150
        # Total: 1550
        for i in range(1, 13):
            round_obj = Round(number=i)
            self.session.add(round_obj)
            self.session.flush()  # Ensure round_id is assigned before creating checks
            check = Check(service=service, round=round_obj, result=True, output="ok", completed=True)
            self.session.add(check)
        self.session.commit()

        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = resp.json

        team_idx = data["labels"].index("Late Phase Team")
        score = int(data["service_scores"][team_idx])

        # Expected: 1000 + 400 + 150 = 1550
        assert score == 1550, f"Expected 1550 with phased multipliers, got {score}"

    def test_api_scoreboard_dynamic_scoring_disabled(self):
        """Test that scores are normal when dynamic scoring is disabled."""

        self.set_setting("sla_enabled", "False")
        self.set_setting("dynamic_scoring_enabled", "False")

        team = Team(name="Normal Team", color="Blue")
        self.session.add(team)
        self.session.commit()

        service = Service(
            name="FTP",
            team=team,
            check_name="FTPCheck",
            host="12.12.12.12",
            port=21,
            points=100,
        )
        self.session.add(service)

        # 3 passing checks = 300 points (no multiplier)
        for i in range(1, 4):
            round_obj = Round(number=i)
            self.session.add(round_obj)
            self.session.flush()  # Ensure round_id is assigned before creating checks
            check = Check(service=service, round=round_obj, result=True, output="ok", completed=True)
            self.session.add(check)
        self.session.commit()

        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = resp.json

        team_idx = data["labels"].index("Normal Team")
        score = int(data["service_scores"][team_idx])

        # Without dynamic scoring: 3 * 100 = 300
        assert score == 300, f"Expected 300 without dynamic scoring, got {score}"

    def test_api_overview_with_dynamic_scoring(self):
        """Test that overview API applies dynamic scoring multipliers."""

        self.set_setting("sla_enabled", "False")
        self.set_setting("dynamic_scoring_enabled", "True")
        self.set_setting("dynamic_scoring_early_rounds", "5")
        self.set_setting("dynamic_scoring_early_multiplier", "3.0")
        self.set_setting("dynamic_scoring_late_start_round", "50")
        self.set_setting("dynamic_scoring_late_multiplier", "0.5")

        team = Team(name="Overview Dynamic Team", color="Blue")
        self.session.add(team)
        self.session.commit()

        service = Service(
            name="DNS",
            team=team,
            check_name="DNSCheck",
            host="13.13.13.13",
            port=53,
            points=100,
        )
        self.session.add(service)

        # 2 rounds in early phase with 3x multiplier
        # Expected: 2 * 100 * 3 = 600
        for i in range(1, 3):
            round_obj = Round(number=i)
            self.session.add(round_obj)
            self.session.flush()  # Ensure round_id is assigned before creating checks
            check = Check(service=service, round=round_obj, result=True, output="ok", completed=True)
            self.session.add(check)
        self.session.commit()

        resp = self.client.get("/api/overview/get_data")
        assert resp.status_code == 200
        data = resp.json

        # Find the score row
        current_scores_row = data["data"][0]  # First row is "Current Score"
        assert current_scores_row[0] == "Current Score"

        # Score should be 600 with 3x multiplier
        # Team appears after "Current Score" label
        team_score = int(current_scores_row[1])
        assert (
            team_score == 600
        ), f"Expected 600 with 3x multiplier in overview, got {team_score}"

    def test_api_service_checks_shows_earned_score(self):
        """Test that /api/service/{id}/checks returns earned_score and multiplier fields."""
        self.login("testuser", "testpass")

        # Enable dynamic scoring
        self.set_setting("dynamic_scoring_enabled", "True")
        self.set_setting("dynamic_scoring_early_rounds", "5")
        self.set_setting("dynamic_scoring_early_multiplier", "2.0")
        self.set_setting("dynamic_scoring_late_start_round", "20")
        self.set_setting("dynamic_scoring_late_multiplier", "0.5")

        team = self.session.query(Team).first()
        service = Service(
            name="Earned Score Test",
            team=team,
            check_name="HTTPCheck",
            host="20.20.20.20",
            port=80,
            points=100,
        )
        self.session.add(service)
        self.session.commit()

        # Create checks in different phases:
        # Round 2 (early): 2x multiplier, pass -> 200 earned
        # Round 10 (normal): 1x multiplier, pass -> 100 earned
        # Round 25 (late): 0.5x multiplier, fail -> 0 earned

        round_early = Round(number=2)
        self.session.add(round_early)
        self.session.flush()
        check_early = Check(service=service, round=round_early)
        check_early.finished(True, "Pass", "ok", "command")
        self.session.add(check_early)

        round_normal = Round(number=10)
        self.session.add(round_normal)
        self.session.flush()
        check_normal = Check(service=service, round=round_normal)
        check_normal.finished(True, "Pass", "ok", "command")
        self.session.add(check_normal)

        round_late = Round(number=25)
        self.session.add(round_late)
        self.session.flush()
        check_late = Check(service=service, round=round_late)
        check_late.finished(False, "Fail", "fail", "command")
        self.session.add(check_late)

        self.session.commit()

        resp = self.client.get(f"/api/service/{service.id}/checks")
        assert resp.status_code == 200
        data = resp.json["data"]

        # Find checks by round number
        check_data = {c["round"]: c for c in data}

        # Early phase check (round 2): passed, 2x multiplier
        assert "earned_score" in check_data[2]
        assert "multiplier" in check_data[2]
        assert check_data[2]["earned_score"] == 200
        assert check_data[2]["multiplier"] == 2.0

        # Normal phase check (round 10): passed, 1x multiplier
        assert check_data[10]["earned_score"] == 100
        assert check_data[10]["multiplier"] == 1.0

        # Late phase check (round 25): failed, 0.5x multiplier but 0 earned
        assert check_data[25]["earned_score"] == 0
        assert check_data[25]["multiplier"] == 0.5

    def test_api_service_checks_without_dynamic_scoring(self):
        """Test that earned_score uses 1x multiplier when dynamic scoring is disabled."""
        self.login("testuser", "testpass")

        # Disable dynamic scoring
        self.set_setting("dynamic_scoring_enabled", "False")

        team = self.session.query(Team).first()
        service = Service(
            name="No Dynamic Test",
            team=team,
            check_name="HTTPCheck",
            host="21.21.21.21",
            port=80,
            points=100,
        )
        self.session.add(service)
        self.session.commit()

        # Create a passing check in what would be "early" phase if enabled
        round_obj = Round(number=1)
        self.session.add(round_obj)
        self.session.flush()
        check = Check(service=service, round=round_obj)
        check.finished(True, "Pass", "ok", "command")
        self.session.add(check)
        self.session.commit()

        resp = self.client.get(f"/api/service/{service.id}/checks")
        assert resp.status_code == 200
        data = resp.json["data"]

        # Without dynamic scoring, multiplier should be 1.0
        assert data[0]["earned_score"] == 100
        assert data[0]["multiplier"] == 1.0

    def test_api_service_checks_with_sla_penalty(self):
        """Test that per-check earned_score reflects SLA penalty based on consecutive failures."""
        self.login("testuser", "testpass")

        # Enable SLA with threshold=1, 10% penalty, additive mode
        self.set_setting("sla_enabled", "True")
        self.set_setting("sla_penalty_threshold", "1")
        self.set_setting("sla_penalty_percent", "10")
        self.set_setting("sla_penalty_max_percent", "50")
        self.set_setting("sla_penalty_mode", "additive")
        self.set_setting("dynamic_scoring_enabled", "False")

        team = self.session.query(Team).first()
        service = Service(
            name="SLA Penalty Test",
            team=team,
            check_name="ICMPCheck",
            host="30.30.30.30",
            port=0,
            points=100,
        )
        self.session.add(service)
        self.session.commit()

        # Create check history: 3 failures, then 1 pass
        # Round 1: Fail
        # Round 2: Fail
        # Round 3: Fail
        # Round 4: Pass (should have 30% penalty: (3-1+1)*10% = 30%)
        for i in range(1, 5):
            round_obj = Round(number=i)
            self.session.add(round_obj)
            self.session.flush()
            result = i == 4  # Only round 4 passes
            check = Check(service=service, round=round_obj)
            check.finished(result, "Test", "ok", "command")
            self.session.add(check)
        self.session.commit()

        resp = self.client.get(f"/api/service/{service.id}/checks")
        assert resp.status_code == 200
        data = resp.json["data"]

        # Data is returned in descending order (most recent first)
        # Round 4 (index 0): Pass with 30% penalty = 70 earned
        assert data[0]["round"] == 4
        assert data[0]["result"] is True
        assert data[0]["earned_score"] == 70, f"Expected 70 (100 - 30% penalty), got {data[0]['earned_score']}"
        assert data[0]["sla_penalty"] == 30

        # Round 3, 2, 1: All failures with 0 earned
        for i, round_num in enumerate([3, 2, 1], start=1):
            assert data[i]["round"] == round_num
            assert data[i]["result"] is False
            assert data[i]["earned_score"] == 0
            assert data[i]["sla_penalty"] == 0

    def test_api_scoreboard_combined_dynamic_and_sla(self):
        """Test scoreboard API with both dynamic scoring AND SLA penalties enabled."""

        # Enable both features
        self.set_setting("sla_enabled", "True")
        self.set_setting("sla_penalty_threshold", "3")
        self.set_setting("sla_penalty_percent", "20")
        self.set_setting("sla_penalty_max_percent", "50")
        self.set_setting("sla_penalty_mode", "additive")
        self.set_setting("sla_allow_negative", "False")

        self.set_setting("dynamic_scoring_enabled", "True")
        self.set_setting("dynamic_scoring_early_rounds", "5")
        self.set_setting("dynamic_scoring_early_multiplier", "2.0")
        self.set_setting("dynamic_scoring_late_start_round", "20")
        self.set_setting("dynamic_scoring_late_multiplier", "0.5")

        # Create a team
        team = Team(name="Combined Test Team", color="Blue")
        self.session.add(team)
        self.session.commit()

        service = Service(
            name="Combined Service",
            team=team,
            check_name="HTTPCheck",
            host="22.22.22.22",
            port=80,
            points=100,
        )
        self.session.add(service)
        self.session.commit()

        # Create 8 rounds (all early phase with 2x multiplier)
        # Rounds 1-3: pass (3 * 100 * 2 = 600)
        # Rounds 4-8: fail (5 consecutive failures, penalty at threshold)
        for i in range(1, 9):
            round_obj = Round(number=i)
            self.session.add(round_obj)
            self.session.flush()
            result = i <= 3  # First 3 pass, then 5 fail
            check = Check(
                service=service, round=round_obj, result=result, output="test", completed=True
            )
            self.session.add(check)
        self.session.commit()

        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = resp.json

        # Both features should be reported as enabled
        assert data["sla_enabled"] is True

        team_idx = data["labels"].index("Combined Test Team")

        # Dynamic base score: 3 passing * 100 pts * 2x = 600
        base_score = int(data["service_scores"][team_idx])
        assert base_score == 600, f"Expected 600 base (3*100*2), got {base_score}"

        # Penalty calculation:
        # Dynamic score: 3 * 100 * 2 = 600
        # 5 consecutive failures, threshold 3 = 2 over
        # Penalty = (2+1)*20% = 60% (capped at 50%)
        # Penalty = 600 * 50% = 300 (based on dynamic score)
        penalty = int(data["sla_penalties"][team_idx])
        assert penalty == 300, f"Expected 300 penalty (50% of 600 dynamic), got {penalty}"

        # Adjusted score: 600 - 300 = 300
        adjusted = int(data["adjusted_scores"][team_idx])
        assert adjusted == 300, f"Expected 300 adjusted (600-300), got {adjusted}"

    def test_api_scoreboard_combined_multiple_phases(self):
        """Test scoreboard with combined features across multiple scoring phases."""

        # Enable both features
        self.set_setting("sla_enabled", "True")
        self.set_setting("sla_penalty_threshold", "5")
        self.set_setting("sla_penalty_percent", "10")
        self.set_setting("sla_penalty_max_percent", "50")
        self.set_setting("sla_penalty_mode", "additive")
        self.set_setting("sla_allow_negative", "False")

        self.set_setting("dynamic_scoring_enabled", "True")
        self.set_setting("dynamic_scoring_early_rounds", "5")
        self.set_setting("dynamic_scoring_early_multiplier", "2.0")
        self.set_setting("dynamic_scoring_late_start_round", "10")
        self.set_setting("dynamic_scoring_late_multiplier", "0.5")

        team = Team(name="Multi Phase Team", color="Blue")
        self.session.add(team)
        self.session.commit()

        service = Service(
            name="Phase Service",
            team=team,
            check_name="SSHCheck",
            host="23.23.23.23",
            port=22,
            points=100,
        )
        self.session.add(service)
        self.session.commit()

        # Create 15 rounds spanning all phases
        # Rounds 1-5: early (2x) - all pass = 5*100*2 = 1000
        # Rounds 6-9: normal (1x) - all pass = 4*100*1 = 400
        # Rounds 10-15: late (0.5x) - first pass then 5 fail = 1*100*0.5 = 50
        # Total dynamic base: 1000 + 400 + 50 = 1450
        #
        # 5 consecutive failures at threshold = 10% penalty
        # Penalty: 1450 * 10% = 145 (based on dynamic score)
        # Adjusted: 1450 - 145 = 1305

        for i in range(1, 16):
            round_obj = Round(number=i)
            self.session.add(round_obj)
            self.session.flush()
            # Pass for rounds 1-10, fail for 11-15
            result = i <= 10
            check = Check(
                service=service, round=round_obj, result=result, output="test", completed=True
            )
            self.session.add(check)
        self.session.commit()

        resp = self.client.get("/api/scoreboard/get_bar_data")
        assert resp.status_code == 200
        data = resp.json

        team_idx = data["labels"].index("Multi Phase Team")

        # Verify dynamic base score with phase multipliers
        base_score = int(data["service_scores"][team_idx])
        assert base_score == 1450, f"Expected 1450 base (1000+400+50), got {base_score}"

        # Verify penalty (5 failures at threshold = 10% of dynamic score)
        penalty = int(data["sla_penalties"][team_idx])
        assert penalty == 145, f"Expected 145 penalty (10% of 1450 dynamic), got {penalty}"

        # Verify adjusted score
        adjusted = int(data["adjusted_scores"][team_idx])
        assert adjusted == 1305, f"Expected 1305 adjusted (1450-145), got {adjusted}"

    def test_ranking_with_ties(self):
        """Test that teams with the same score get the same rank."""
        self.login("testuser", "testpass")

        # Create 4 teams with scores that will result in ties
        # Team A: 200 points (rank 1)
        # Team B: 150 points (rank 2, tied)
        # Team C: 150 points (rank 2, tied)
        # Team D: 100 points (rank 4, skipping 3 due to tie)
        teams_data = [
            ("Team A", 2),   # 2 passes * 100 = 200
            ("Team B", 1),   # 1 pass * 100 = 100... wait, need to recalculate
            ("Team C", 1),   # 1 pass * 100 = 100
            ("Team D", 0),   # 0 passes = 0
        ]

        # Actually, let's make this simpler - use points per service to control scores
        team_a = Team(name="Rank Team A", color="Blue")
        team_b = Team(name="Rank Team B", color="Blue")
        team_c = Team(name="Rank Team C", color="Blue")
        team_d = Team(name="Rank Team D", color="Blue")
        self.session.add_all([team_a, team_b, team_c, team_d])
        self.session.commit()

        # Create services with same name but different teams
        # This tests the per-service ranking in /api/team/{id}/services
        for team, points in [(team_a, 200), (team_b, 150), (team_c, 150), (team_d, 100)]:
            service = Service(
                name="Rank Test Service",
                team=team,
                check_name="HTTPCheck",
                host="40.40.40.40",
                port=80,
                points=points,
            )
            self.session.add(service)
        self.session.commit()

        # Create a round with passing checks for all teams
        round_obj = Round(number=1)
        self.session.add(round_obj)
        self.session.flush()

        for team in [team_a, team_b, team_c, team_d]:
            service = self.session.query(Service).filter(
                Service.team_id == team.id,
                Service.name == "Rank Test Service"
            ).first()
            check = Check(service=service, round=round_obj)
            check.finished(True, "Pass", "ok", "cmd")
            self.session.add(check)
        self.session.commit()

        # Now test that rankings are correct
        # Team A: 200 -> rank 1
        # Team B: 150 -> rank 2 (tied)
        # Team C: 150 -> rank 2 (tied)
        # Team D: 100 -> rank 4 (skips 3)

        # Test via the Service.rank property
        service_a = self.session.query(Service).filter(Service.team_id == team_a.id).first()
        service_b = self.session.query(Service).filter(Service.team_id == team_b.id).first()
        service_c = self.session.query(Service).filter(Service.team_id == team_c.id).first()
        service_d = self.session.query(Service).filter(Service.team_id == team_d.id).first()

        assert service_a.rank == 1, f"Team A should be rank 1, got {service_a.rank}"
        assert service_b.rank == 2, f"Team B should be rank 2 (tied), got {service_b.rank}"
        assert service_c.rank == 2, f"Team C should be rank 2 (tied), got {service_c.rank}"
        assert service_d.rank == 4, f"Team D should be rank 4 (after tie), got {service_d.rank}"

    def test_overview_get_data_service_status_uses_round_number_not_id(self):
        """Test that service status in /api/overview/get_data uses Round.number, not Round.id.

        This is a regression test for a bug where the query was filtering on
        Check.round_id == last_round, but last_round contains Round.number.
        After round 1, these values diverge because each team's checks create
        separate Round objects with the same number but different IDs.

        The bug caused only team 1's service status to show correctly (where
        Round.id == Round.number by coincidence), while other teams showed
        stale or missing data.
        """
        # Disable all scoring features for simpler test
        self.set_setting("sla_enabled", "False")
        self.set_setting("dynamic_scoring_enabled", "False")

        # Create 3 blue teams - this is key to reproducing the bug
        # Each team will have its own Round objects with the same numbers
        team1 = Team(name="Bug Test Team 1", color="Blue")
        team2 = Team(name="Bug Test Team 2", color="Blue")
        team3 = Team(name="Bug Test Team 3", color="Blue")
        self.session.add_all([team1, team2, team3])
        self.session.commit()

        # Create a service for each team with the same name
        services = {}
        for team in [team1, team2, team3]:
            service = Service(
                name="WebService",
                team=team,
                check_name="HTTPCheck",
                host=f"50.50.50.{team.id}",
                port=80,
                points=100,
            )
            self.session.add(service)
            services[team.name] = service
        self.session.commit()

        # Create rounds 1-3 for EACH team (simulating how the engine works)
        # This causes Round.id != Round.number for teams 2 and 3
        # Team 1: Round ids 1,2,3 with numbers 1,2,3
        # Team 2: Round ids 4,5,6 with numbers 1,2,3
        # Team 3: Round ids 7,8,9 with numbers 1,2,3
        expected_last_round_status = {
            "Bug Test Team 1": True,   # Team 1 passes in round 3
            "Bug Test Team 2": False,  # Team 2 fails in round 3
            "Bug Test Team 3": True,   # Team 3 passes in round 3
        }

        for team in [team1, team2, team3]:
            for round_num in range(1, 4):
                round_obj = Round(number=round_num)
                self.session.add(round_obj)
                self.session.flush()

                # Rounds 1-2: all pass
                # Round 3: use expected_last_round_status
                if round_num < 3:
                    result = True
                else:
                    result = expected_last_round_status[team.name]

                check = Check(
                    service=services[team.name],
                    round=round_obj,
                    result=result,
                    output="test",
                    completed=True,
                )
                self.session.add(check)
            self.session.commit()

        # Verify the ID/number divergence exists for team 2 and 3
        # Query the last round (number=3) for each team to verify IDs differ
        team2_round3 = (
            self.session.query(Round)
            .join(Check)
            .filter(Check.service_id == services["Bug Test Team 2"].id)
            .filter(Round.number == 3)
            .first()
        )
        assert team2_round3.id != 3, (
            f"Test setup: Team 2's Round 3 should have id != 3, got {team2_round3.id}"
        )

        cache.clear()

        # Call the API
        resp = self.client.get("/api/overview/get_data")
        assert resp.status_code == 200
        data = resp.json

        # Find the WebService row
        webservice_row = None
        for row in data["data"]:
            if row[0] == "WebService":
                webservice_row = row
                break

        assert webservice_row is not None, (
            f"WebService not found in response. Response data: {data}"
        )

        # Verify each team's service status matches expected
        # Teams are ordered by team.id in the response
        teams_by_id = sorted([team1, team2, team3], key=lambda t: t.id)
        for i, team in enumerate(teams_by_id, start=1):
            actual_status = webservice_row[i]
            expected_status = expected_last_round_status[team.name]
            assert actual_status == expected_status, (
                f"{team.name}: expected status {expected_status}, got {actual_status}. "
                f"This indicates the query is using Round.id instead of Round.number."
            )

    def test_overview_get_data_up_down_ratio_uses_round_number(self):
        """Test that Up/Down ratio in /api/overview/get_data also uses Round.number correctly.

        The num_up_services and num_down_services queries must also use
        Round.number (not Round.id) to correctly count service status for
        the current round.
        """
        self.set_setting("sla_enabled", "False")
        self.set_setting("dynamic_scoring_enabled", "False")

        # Create 2 teams to cause Round.id divergence
        team1 = Team(name="Ratio Team 1", color="Blue")
        team2 = Team(name="Ratio Team 2", color="Blue")
        self.session.add_all([team1, team2])
        self.session.commit()

        # Create 3 services for team 2 (we'll verify team 2's ratio)
        service1 = Service(
            name="Service1", team=team2, check_name="HTTPCheck", host="60.1.1.1", port=80, points=100
        )
        service2 = Service(
            name="Service2", team=team2, check_name="HTTPCheck", host="60.1.1.2", port=80, points=100
        )
        service3 = Service(
            name="Service3", team=team2, check_name="HTTPCheck", host="60.1.1.3", port=80, points=100
        )
        # Create 1 service for team 1 (just to create Round ID divergence)
        service_t1 = Service(
            name="Service1", team=team1, check_name="HTTPCheck", host="60.0.0.1", port=80, points=100
        )
        self.session.add_all([service1, service2, service3, service_t1])
        self.session.commit()

        # Create rounds for team 1 first (this pushes IDs ahead)
        for round_num in range(1, 4):
            round_obj = Round(number=round_num)
            self.session.add(round_obj)
            self.session.flush()
            check = Check(service=service_t1, round=round_obj, result=True, output="ok", completed=True)
            self.session.add(check)
        self.session.commit()

        # Now create rounds for team 2
        # Round 3 (the last) will have id != 3
        for round_num in range(1, 4):
            round_obj = Round(number=round_num)
            self.session.add(round_obj)
            self.session.flush()

            if round_num < 3:
                # Rounds 1-2: all services up
                for svc in [service1, service2, service3]:
                    check = Check(service=svc, round=round_obj, result=True, output="ok", completed=True)
                    self.session.add(check)
            else:
                # Round 3: 2 UP, 1 DOWN
                check1 = Check(service=service1, round=round_obj, result=True, output="ok", completed=True)
                check2 = Check(service=service2, round=round_obj, result=True, output="ok", completed=True)
                check3 = Check(service=service3, round=round_obj, result=False, output="fail", completed=True)
                self.session.add_all([check1, check2, check3])

                # Verify ID divergence
                assert round_obj.id != 3, f"Test setup: expected Round.id != 3, got {round_obj.id}"
        self.session.commit()

        cache.clear()

        resp = self.client.get("/api/overview/get_data")
        assert resp.status_code == 200
        data = resp.json

        # Find Up/Down Ratio row
        ratio_row = None
        for row in data["data"]:
            if row[0] == "Up/Down Ratio":
                ratio_row = row
                break

        assert ratio_row is not None, "Up/Down Ratio row not found"

        # Find team 2's index (teams ordered by id)
        team2_idx = 2 if team1.id < team2.id else 1

        # The ratio string should show "2 up / 1 down" for team 2 in round 3
        # Format: '<span class="text-success">2 <span...></span> / <span class="text-danger">1 <span...></span>'
        team_ratio = ratio_row[team2_idx]
        assert ">2 <" in team_ratio, f"Expected 2 services up for team 2, got: {team_ratio}"
        assert ">1 <" in team_ratio, f"Expected 1 service down for team 2, got: {team_ratio}"

    def test_overview_get_data_multiple_teams_all_services_correct(self):
        """Comprehensive test: multiple teams, multiple services, ID divergence.

        This test creates multiple blue teams with multiple services each,
        and verifies that ALL service statuses are correctly shown for ALL
        teams based on the actual check results from the last round (by number).
        """
        self.set_setting("sla_enabled", "False")
        self.set_setting("dynamic_scoring_enabled", "False")

        # Create 3 blue teams
        team1 = Team(name="Multi Alpha", color="Blue")
        team2 = Team(name="Multi Beta", color="Blue")
        team3 = Team(name="Multi Gamma", color="Blue")
        self.session.add_all([team1, team2, team3])
        self.session.commit()

        # Create 2 services per team
        services = {}
        for team in [team1, team2, team3]:
            http_svc = Service(
                name="HTTP",
                team=team,
                check_name="HTTPCheck",
                host=f"70.70.1.{team.id}",
                port=80,
                points=100,
            )
            ssh_svc = Service(
                name="SSH",
                team=team,
                check_name="SSHCheck",
                host=f"70.70.2.{team.id}",
                port=22,
                points=100,
            )
            self.session.add_all([http_svc, ssh_svc])
            services[(team.name, "HTTP")] = http_svc
            services[(team.name, "SSH")] = ssh_svc
        self.session.commit()

        # Create rounds for each team sequentially to cause ID divergence
        # Expected status in the last round (round 3)
        expected_status = {
            ("Multi Alpha", "HTTP"): True,
            ("Multi Alpha", "SSH"): False,
            ("Multi Beta", "HTTP"): False,
            ("Multi Beta", "SSH"): True,
            ("Multi Gamma", "HTTP"): True,
            ("Multi Gamma", "SSH"): True,
        }

        for team in [team1, team2, team3]:
            for round_num in range(1, 4):
                round_obj = Round(number=round_num)
                self.session.add(round_obj)
                self.session.flush()

                for svc_name in ["HTTP", "SSH"]:
                    service = services[(team.name, svc_name)]
                    if round_num < 3:
                        # Rounds 1-2: all pass
                        result = True
                    else:
                        # Round 3: use expected status
                        result = expected_status[(team.name, svc_name)]

                    check = Check(
                        service=service,
                        round=round_obj,
                        result=result,
                        output="test",
                        completed=True,
                    )
                    self.session.add(check)
            self.session.commit()

        # Verify ID divergence for teams 2 and 3
        team2_round3 = (
            self.session.query(Round)
            .join(Check)
            .filter(Check.service_id == services[("Multi Beta", "HTTP")].id)
            .filter(Round.number == 3)
            .first()
        )
        assert team2_round3.id != 3, (
            f"Test setup: Team 2's Round 3 should have id != 3, got {team2_round3.id}"
        )

        cache.clear()

        resp = self.client.get("/api/overview/get_data")
        assert resp.status_code == 200
        data = resp.json

        # Find HTTP and SSH service rows
        http_row = None
        ssh_row = None
        for row in data["data"]:
            if row[0] == "HTTP":
                http_row = row
            elif row[0] == "SSH":
                ssh_row = row

        assert http_row is not None, "HTTP service not found in response"
        assert ssh_row is not None, "SSH service not found in response"

        # Verify each team's service status
        teams_by_id = sorted([team1, team2, team3], key=lambda t: t.id)
        for i, team in enumerate(teams_by_id, start=1):
            # Check HTTP
            actual_http = http_row[i]
            expected_http = expected_status[(team.name, "HTTP")]
            assert actual_http == expected_http, (
                f"{team.name} HTTP: expected {expected_http}, got {actual_http}"
            )

            # Check SSH
            actual_ssh = ssh_row[i]
            expected_ssh = expected_status[(team.name, "SSH")]
            assert actual_ssh == expected_ssh, (
                f"{team.name} SSH: expected {expected_ssh}, got {actual_ssh}"
            )
