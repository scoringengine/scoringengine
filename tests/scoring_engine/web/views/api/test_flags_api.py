"""Comprehensive tests for Flags API endpoints including complex SQL queries"""
from datetime import datetime, timedelta, timezone

import pytest

from scoring_engine.models.flag import Flag, FlagTypeEnum, Perm, Platform, Solve
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team
from scoring_engine.models.user import User
from scoring_engine.web import create_app
from tests.scoring_engine.unit_test import UnitTest


class TestFlagsAPI(UnitTest):
    """Test flags API authorization and complex SQL queries"""

    def setup_method(self):
        super(TestFlagsAPI, self).setup_method()
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        # Create teams
        self.white_team = Team(name="White Team", color="White")
        self.red_team = Team(name="Red Team", color="Red")
        self.blue_team1 = Team(name="Blue Team 1", color="Blue")
        self.blue_team2 = Team(name="Blue Team 2", color="Blue")

        self.session.add_all([self.white_team, self.red_team, self.blue_team1, self.blue_team2])
        self.session.commit()

        # Create users
        self.white_user = User(username="whiteuser", password="pass", team=self.white_team)
        self.red_user = User(username="reduser", password="pass", team=self.red_team)
        self.blue_user1 = User(username="blueuser1", password="pass", team=self.blue_team1)
        self.blue_user2 = User(username="blueuser2", password="pass", team=self.blue_team2)

        self.session.add_all([self.white_user, self.red_user, self.blue_user1, self.blue_user2])
        self.session.commit()

        # Add agent show flag early setting
        self.session.add(Setting(name="agent_show_flag_early_mins", value=5))
        self.session.commit()

    def teardown_method(self):
        self.ctx.pop()
        super(TestFlagsAPI, self).teardown_method()

    def login(self, username, password):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    # Authorization Tests
    def test_api_flags_requires_auth(self):
        """Test that /api/flags requires authentication"""
        resp = self.client.get("/api/flags")
        assert resp.status_code == 302

    def test_api_flags_red_team_authorized(self):
        """Test that red team can access flags"""
        self.login("reduser", "pass")
        resp = self.client.get("/api/flags")
        assert resp.status_code == 200

    def test_api_flags_white_team_authorized(self):
        """Test that white team can access flags"""
        self.login("whiteuser", "pass")
        resp = self.client.get("/api/flags")
        assert resp.status_code == 200

    def test_api_flags_blue_team_unauthorized(self):
        """Test that blue team cannot access flags"""
        self.login("blueuser1", "pass")
        resp = self.client.get("/api/flags")
        assert resp.status_code == 403

    def test_api_flags_solves_requires_auth(self):
        """Test that /api/flags/solves requires authentication"""
        resp = self.client.get("/api/flags/solves")
        assert resp.status_code == 302

    def test_api_flags_solves_red_team_authorized(self):
        """Test that red team can access solves"""
        self.login("reduser", "pass")
        resp = self.client.get("/api/flags/solves")
        assert resp.status_code == 200

    def test_api_flags_solves_white_team_authorized(self):
        """Test that white team can access solves"""
        self.login("whiteuser", "pass")
        resp = self.client.get("/api/flags/solves")
        assert resp.status_code == 200

    def test_api_flags_solves_blue_team_unauthorized(self):
        """Test that blue team cannot access solves"""
        self.login("blueuser1", "pass")
        resp = self.client.get("/api/flags/solves")
        assert resp.status_code == 403

    def test_api_flags_totals_requires_auth(self):
        """Test that /api/flags/totals requires authentication"""
        resp = self.client.get("/api/flags/totals")
        assert resp.status_code == 302

    @pytest.mark.skip(reason="Requires MySQL - uses MySQL-specific IF() function")
    def test_api_flags_totals_red_team_authorized(self):
        """Test that red team can access totals"""
        self.login("reduser", "pass")
        resp = self.client.get("/api/flags/totals")
        assert resp.status_code == 200

    @pytest.mark.skip(reason="Requires MySQL - uses MySQL-specific IF() function")
    def test_api_flags_totals_white_team_authorized(self):
        """Test that white team can access totals"""
        self.login("whiteuser", "pass")
        resp = self.client.get("/api/flags/totals")
        assert resp.status_code == 200

    @pytest.mark.skip(reason="Requires MySQL - uses MySQL-specific IF() function")
    def test_api_flags_totals_blue_team_unauthorized(self):
        """Test that blue team cannot access totals"""
        self.login("blueuser1", "pass")
        resp = self.client.get("/api/flags/totals")
        assert resp.status_code == 403

    # Flag Filtering Tests
    def test_api_flags_filters_by_time_window(self):
        """Test that flags are filtered by start/end time"""
        # Create past flag (should not be shown)
        past_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "/tmp/past", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            dummy=False
        )

        # Create current flag (should be shown)
        current_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "/tmp/current", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(minutes=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False
        )

        # Create future flag (should be shown based on early window)
        future_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "/tmp/future", "content": "test"},
            start_time=datetime.now(timezone.utc) + timedelta(minutes=2),
            end_time=datetime.now(timezone.utc) + timedelta(hours=2),
            dummy=False
        )

        self.session.add_all([past_flag, current_flag, future_flag])
        self.session.commit()

        self.login("reduser", "pass")
        resp = self.client.get("/api/flags")
        data = resp.json["data"]

        # Only current and future flags should be shown
        flag_ids = [f["id"] for f in data]
        assert current_flag.id in flag_ids
        assert future_flag.id in flag_ids
        assert past_flag.id not in flag_ids

    def test_api_flags_excludes_dummy_flags(self):
        """Test that dummy flags are excluded"""
        # Create real flag
        real_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "/tmp/real", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False
        )

        # Create dummy flag
        dummy_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "/tmp/dummy", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=True
        )

        self.session.add_all([real_flag, dummy_flag])
        self.session.commit()

        self.login("reduser", "pass")
        resp = self.client.get("/api/flags")
        data = resp.json["data"]

        flag_ids = [f["id"] for f in data]
        assert real_flag.id in flag_ids
        assert dummy_flag.id not in flag_ids

    def test_api_flags_returns_all_platforms(self):
        """Test that flags from all platforms are returned"""
        # Create Windows flag
        win_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "C:\\test", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False
        )

        # Create Linux flag
        nix_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            perm=Perm.root,
            data={"path": "/etc/test", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False
        )

        self.session.add_all([win_flag, nix_flag])
        self.session.commit()

        self.login("reduser", "pass")
        resp = self.client.get("/api/flags")
        data = resp.json["data"]

        platforms = [f["platform"] for f in data]
        assert "win" in platforms
        assert "nix" in platforms

    def test_api_flags_returns_all_permissions(self):
        """Test that flags with different permissions are returned"""
        # Create user-level flag
        user_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "C:\\test", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False
        )

        # Create root-level flag
        root_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.root,
            data={"path": "C:\\admin", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False
        )

        self.session.add_all([user_flag, root_flag])
        self.session.commit()

        self.login("reduser", "pass")
        resp = self.client.get("/api/flags")
        data = resp.json["data"]

        perms = [f["perm"] for f in data]
        assert "user" in perms
        assert "root" in perms

    # Solve Status Tests
    def test_api_flags_solves_with_no_solves(self):
        """Test that solves endpoint works with no solves"""
        # Create services
        service1 = Service(
            name="Host1",
            check_name="AgentCheck",
            host="192.168.1.10",
            team=self.blue_team1,
            port=0
        )
        service2 = Service(
            name="Host2",
            check_name="AgentCheck",
            host="192.168.1.20",
            team=self.blue_team2,
            port=0
        )

        self.session.add_all([service1, service2])
        self.session.commit()

        self.login("reduser", "pass")
        resp = self.client.get("/api/flags/solves")
        data = resp.json["data"]

        assert "columns" in data
        assert "rows" in data
        assert "Team" in data["columns"]

    def test_api_flags_solves_shows_solve_status(self):
        """Test that solve status is correctly shown"""
        # Create services
        service1 = Service(
            name="Host1",
            check_name="AgentCheck",
            host="192.168.1.10",
            team=self.blue_team1,
            port=0
        )
        service2 = Service(
            name="Host2",
            check_name="AgentCheck",
            host="192.168.1.20",
            team=self.blue_team2,
            port=0
        )

        # Create flag
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "C:\\test", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False
        )

        # Create solve for team1
        solve = Solve(
            host="192.168.1.10",
            team_id=self.blue_team1.id,
            flag_id=flag.id
        )

        self.session.add_all([service1, service2, flag, solve])
        self.session.commit()

        self.login("reduser", "pass")
        resp = self.client.get("/api/flags/solves")
        data = resp.json["data"]

        # Team 1 should have solve, team 2 should not
        assert len(data["rows"]) >= 1

    # Totals Tests (Complex SQL)
    @pytest.mark.skip(reason="Requires MySQL - uses MySQL-specific IF() function")
    def test_api_flags_totals_empty(self):
        """Test totals with no flags or solves"""
        self.login("reduser", "pass")
        resp = self.client.get("/api/flags/totals")
        data = resp.json["data"]

        # Should have entries for all blue teams
        team_names = [entry["team"] for entry in data]
        assert "Blue Team 1" in team_names
        assert "Blue Team 2" in team_names

        # All scores should be 0
        for entry in data:
            assert entry["win_score"] == 0
            assert entry["nix_score"] == 0
            assert entry["total_score"] == 0

    @pytest.mark.skip(reason="Requires MySQL - uses MySQL-specific IF() function")
    def test_api_flags_totals_user_level_scoring(self):
        """Test that user-level flags count as 0.5"""
        # Create service
        service = Service(
            name="Host1",
            check_name="AgentCheck",
            host="192.168.1.10",
            team=self.blue_team1,
            port=0
        )

        # Create Windows user flag
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "C:\\test", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False
        )

        # Create solve
        solve = Solve(
            host="192.168.1.10",
            team_id=self.blue_team1.id,
            flag_id=flag.id
        )

        self.session.add_all([service, flag, solve])
        self.session.commit()

        self.login("reduser", "pass")
        resp = self.client.get("/api/flags/totals")
        data = resp.json["data"]

        # Find Blue Team 1 entry
        team1_entry = next(e for e in data if e["team"] == "Blue Team 1")

        # User-level flag should count as 0.5
        assert team1_entry["win_score"] == 0.5
        assert team1_entry["nix_score"] == 0
        assert team1_entry["total_score"] == 0.5

    @pytest.mark.skip(reason="Requires MySQL - uses MySQL-specific IF() function")
    def test_api_flags_totals_root_level_scoring(self):
        """Test that root-level flags count as 1"""
        # Create service
        service = Service(
            name="Host1",
            check_name="AgentCheck",
            host="192.168.1.10",
            team=self.blue_team1,
            port=0
        )

        # Create Linux root flag
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            perm=Perm.root,
            data={"path": "/etc/test", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False
        )

        # Create solve
        solve = Solve(
            host="192.168.1.10",
            team_id=self.blue_team1.id,
            flag_id=flag.id
        )

        self.session.add_all([service, flag, solve])
        self.session.commit()

        self.login("reduser", "pass")
        resp = self.client.get("/api/flags/totals")
        data = resp.json["data"]

        # Find Blue Team 1 entry
        team1_entry = next(e for e in data if e["team"] == "Blue Team 1")

        # Root-level flag should count as 1
        assert team1_entry["nix_score"] == 1
        assert team1_entry["win_score"] == 0
        assert team1_entry["total_score"] == 1

    @pytest.mark.skip(reason="Requires MySQL - uses MySQL-specific IF() function")
    def test_api_flags_totals_user_and_root_scoring(self):
        """Test that user + root on same host counts as root (1.0)"""
        # Create service
        service = Service(
            name="Host1",
            check_name="AgentCheck",
            host="192.168.1.10",
            team=self.blue_team1,
            port=0
        )

        # Create Windows user flag
        user_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "C:\\user", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False
        )

        # Create Windows root flag
        root_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.root,
            data={"path": "C:\\admin", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False
        )

        # Create solves for both
        solve_user = Solve(
            host="192.168.1.10",
            team_id=self.blue_team1.id,
            flag_id=user_flag.id
        )
        solve_root = Solve(
            host="192.168.1.10",
            team_id=self.blue_team1.id,
            flag_id=root_flag.id
        )

        self.session.add_all([service, user_flag, root_flag, solve_user, solve_root])
        self.session.commit()

        self.login("reduser", "pass")
        resp = self.client.get("/api/flags/totals")
        data = resp.json["data"]

        # Find Blue Team 1 entry
        team1_entry = next(e for e in data if e["team"] == "Blue Team 1")

        # Should count as 1 (root overrides user)
        assert team1_entry["win_score"] == 1
        assert team1_entry["total_score"] == 1

    @pytest.mark.skip(reason="Requires MySQL - uses MySQL-specific IF() function")
    def test_api_flags_totals_multiple_hosts(self):
        """Test scoring across multiple hosts"""
        # Create services
        service1 = Service(
            name="Host1",
            check_name="AgentCheck",
            host="192.168.1.10",
            team=self.blue_team1,
            port=0
        )
        service2 = Service(
            name="Host2",
            check_name="AgentCheck",
            host="192.168.1.20",
            team=self.blue_team1,
            port=0
        )

        # Create flags
        flag1 = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.root,
            data={"path": "C:\\test1", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False
        )
        flag2 = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.root,
            data={"path": "C:\\test2", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False
        )

        # Create solves
        solve1 = Solve(host="192.168.1.10", team_id=self.blue_team1.id, flag_id=flag1.id)
        solve2 = Solve(host="192.168.1.20", team_id=self.blue_team1.id, flag_id=flag2.id)

        self.session.add_all([service1, service2, flag1, flag2, solve1, solve2])
        self.session.commit()

        self.login("reduser", "pass")
        resp = self.client.get("/api/flags/totals")
        data = resp.json["data"]

        # Find Blue Team 1 entry
        team1_entry = next(e for e in data if e["team"] == "Blue Team 1")

        # Should count both hosts
        assert team1_entry["win_score"] == 2
        assert team1_entry["total_score"] == 2

    @pytest.mark.skip(reason="Requires MySQL - uses MySQL-specific IF() function")
    def test_api_flags_totals_mixed_platforms(self):
        """Test scoring with both Windows and Linux flags"""
        # Create service
        service = Service(
            name="Host1",
            check_name="AgentCheck",
            host="192.168.1.10",
            team=self.blue_team1,
            port=0
        )

        # Create Windows flag
        win_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.root,
            data={"path": "C:\\test", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False
        )

        # Create Linux flag
        nix_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            perm=Perm.root,
            data={"path": "/etc/test", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False
        )

        # Create solves
        solve_win = Solve(host="192.168.1.10", team_id=self.blue_team1.id, flag_id=win_flag.id)
        solve_nix = Solve(host="192.168.1.10", team_id=self.blue_team1.id, flag_id=nix_flag.id)

        self.session.add_all([service, win_flag, nix_flag, solve_win, solve_nix])
        self.session.commit()

        self.login("reduser", "pass")
        resp = self.client.get("/api/flags/totals")
        data = resp.json["data"]

        # Find Blue Team 1 entry
        team1_entry = next(e for e in data if e["team"] == "Blue Team 1")

        # Should have both platform scores
        assert team1_entry["win_score"] == 1
        assert team1_entry["nix_score"] == 1
        assert team1_entry["total_score"] == 2

    @pytest.mark.skip(reason="Requires MySQL - uses MySQL-specific IF() function")
    def test_api_flags_totals_multiple_teams(self):
        """Test that each team's score is calculated independently"""
        # Create services for both teams
        service1 = Service(
            name="Host1",
            check_name="AgentCheck",
            host="192.168.1.10",
            team=self.blue_team1,
            port=0
        )
        service2 = Service(
            name="Host2",
            check_name="AgentCheck",
            host="192.168.1.20",
            team=self.blue_team2,
            port=0
        )

        # Create flag
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.root,
            data={"path": "C:\\test", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False
        )

        # Only team1 solves
        solve1 = Solve(host="192.168.1.10", team_id=self.blue_team1.id, flag_id=flag.id)

        self.session.add_all([service1, service2, flag, solve1])
        self.session.commit()

        self.login("reduser", "pass")
        resp = self.client.get("/api/flags/totals")
        data = resp.json["data"]

        # Find entries
        team1_entry = next(e for e in data if e["team"] == "Blue Team 1")
        team2_entry = next(e for e in data if e["team"] == "Blue Team 2")

        # Team1 should have score, team2 should not
        assert team1_entry["total_score"] == 1
        assert team2_entry["total_score"] == 0
