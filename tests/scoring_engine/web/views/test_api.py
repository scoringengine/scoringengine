import json
from datetime import datetime, timedelta, timezone

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
        setting = Setting.get_setting(name)
        if setting:
            # Convert string "True"/"False" to bool for boolean settings
            if value == "True":
                setting.value = True
            elif value == "False":
                setting.value = False
            else:
                setting.value = value
            self.session.commit()
        Setting.clear_cache()

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
            # First 2 rounds pass, rounds 3-6 fail (4 consecutive failures)
            result = i <= 2
            check = Check(
                service=service1, round=round_obj, result=result, output="test"
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
            # Team 1: All pass
            check1 = Check(service=service1, round=round_obj, result=True, output="ok")
            # Team 2: Pass, pass, fail, pass, fail (no consecutive >= threshold)
            check2_result = i not in [3, 5]
            check2 = Check(
                service=service2, round=round_obj, result=check2_result, output="ok"
            )
            # Team 3: Pass, fail, fail, fail, fail (4 consecutive failures)
            check3_result = i == 1
            check3 = Check(
                service=service3, round=round_obj, result=check3_result, output="ok"
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
            result = i == 1  # Only first round passes
            check = Check(
                service=service, round=round_obj, result=result, output="test"
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
            check1 = Check(
                service=service1, round=round_obj, result=False, output="fail"
            )
            check2 = Check(service=service2, round=round_obj, result=True, output="ok")
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
            check = Check(service=service, round=round_obj, result=True, output="ok")
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
            check = Check(service=service, round=round_obj, result=True, output="ok")
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
            check = Check(service=service, round=round_obj, result=True, output="ok")
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
            check = Check(service=service, round=round_obj, result=True, output="ok")
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
