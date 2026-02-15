"""Comprehensive tests for Flags API endpoints including complex SQL queries"""

from datetime import datetime, timedelta, timezone

import pytest

from scoring_engine.db import db
from scoring_engine.models.flag import Flag, FlagTypeEnum, Perm, Platform, Solve
from scoring_engine.models.service import Service
from scoring_engine.models.setting import Setting
from scoring_engine.models.team import Team
from scoring_engine.models.user import User


class TestFlagsAPI:
    """Test flags API authorization and complex SQL queries"""

    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session):
        self.client = test_client

        # Create teams
        self.white_team = Team(name="White Team", color="White")
        self.red_team = Team(name="Red Team", color="Red")
        self.blue_team1 = Team(name="Blue Team 1", color="Blue")
        self.blue_team2 = Team(name="Blue Team 2", color="Blue")
        db.session.add_all([self.white_team, self.red_team, self.blue_team1, self.blue_team2])
        db.session.commit()

        # Create users
        self.white_user = User(username="whiteuser", password="testpass", team=self.white_team)
        self.red_user = User(username="reduser", password="testpass", team=self.red_team)
        self.blue_user1 = User(username="blueuser1", password="testpass", team=self.blue_team1)
        self.blue_user2 = User(username="blueuser2", password="testpass", team=self.blue_team2)
        db.session.add_all([self.white_user, self.red_user, self.blue_user1, self.blue_user2])
        db.session.commit()

        # Add agent show flag early setting
        db.session.add(Setting(name="agent_show_flag_early_mins", value=5))
        db.session.commit()

    def login(self, username, password="testpass"):
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
        self.login("reduser")
        resp = self.client.get("/api/flags")
        assert resp.status_code == 200

    def test_api_flags_white_team_authorized(self):
        """Test that white team can access flags"""
        self.login("whiteuser")
        resp = self.client.get("/api/flags")
        assert resp.status_code == 200

    def test_api_flags_blue_team_unauthorized(self):
        """Test that blue team cannot access flags"""
        self.login("blueuser1")
        resp = self.client.get("/api/flags")
        assert resp.status_code == 403

    def test_api_flags_solves_requires_auth(self):
        """Test that /api/flags/solves requires authentication"""
        resp = self.client.get("/api/flags/solves")
        assert resp.status_code == 302

    def test_api_flags_solves_red_team_authorized(self):
        """Test that red team can access solves"""
        self.login("reduser")
        resp = self.client.get("/api/flags/solves")
        assert resp.status_code == 200

    def test_api_flags_solves_white_team_authorized(self):
        """Test that white team can access solves"""
        self.login("whiteuser")
        resp = self.client.get("/api/flags/solves")
        assert resp.status_code == 200

    def test_api_flags_solves_blue_team_unauthorized(self):
        """Test that blue team cannot access solves"""
        self.login("blueuser1")
        resp = self.client.get("/api/flags/solves")
        assert resp.status_code == 403

    def test_api_flags_totals_requires_auth(self):
        """Test that /api/flags/totals requires authentication"""
        resp = self.client.get("/api/flags/totals")
        assert resp.status_code == 302

    @pytest.mark.skip(reason="Requires MySQL - uses MySQL-specific IF() function")
    def test_api_flags_totals_red_team_authorized(self):
        """Test that red team can access totals"""
        self.login("reduser")
        resp = self.client.get("/api/flags/totals")
        assert resp.status_code == 200

    @pytest.mark.skip(reason="Requires MySQL - uses MySQL-specific IF() function")
    def test_api_flags_totals_white_team_authorized(self):
        """Test that white team can access totals"""
        self.login("whiteuser")
        resp = self.client.get("/api/flags/totals")
        assert resp.status_code == 200

    @pytest.mark.skip(reason="Requires MySQL - uses MySQL-specific IF() function")
    def test_api_flags_totals_blue_team_unauthorized(self):
        """Test that blue team cannot access totals"""
        self.login("blueuser1")
        resp = self.client.get("/api/flags/totals")
        assert resp.status_code == 403

    # Flag Filtering Tests
    def test_api_flags_filters_by_time_window(self):
        """Test that flags are filtered by start/end time"""
        past_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "/tmp/past", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            dummy=False,
        )
        current_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "/tmp/current", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(minutes=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False,
        )
        future_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "/tmp/future", "content": "test"},
            start_time=datetime.now(timezone.utc) + timedelta(minutes=2),
            end_time=datetime.now(timezone.utc) + timedelta(hours=2),
            dummy=False,
        )
        db.session.add_all([past_flag, current_flag, future_flag])
        db.session.commit()

        self.login("reduser")
        resp = self.client.get("/api/flags")
        data = resp.json["data"]

        flag_ids = [f["id"] for f in data]
        assert current_flag.id in flag_ids
        assert future_flag.id in flag_ids
        assert past_flag.id not in flag_ids

    def test_api_flags_excludes_dummy_flags(self):
        """Test that dummy flags are excluded"""
        real_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "/tmp/real", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False,
        )
        dummy_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "/tmp/dummy", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=True,
        )
        db.session.add_all([real_flag, dummy_flag])
        db.session.commit()

        self.login("reduser")
        resp = self.client.get("/api/flags")
        data = resp.json["data"]

        flag_ids = [f["id"] for f in data]
        assert real_flag.id in flag_ids
        assert dummy_flag.id not in flag_ids

    def test_api_flags_returns_all_platforms(self):
        """Test that flags from all platforms are returned"""
        win_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "C:\\test", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False,
        )
        nix_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            perm=Perm.root,
            data={"path": "/etc/test", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False,
        )
        db.session.add_all([win_flag, nix_flag])
        db.session.commit()

        self.login("reduser")
        resp = self.client.get("/api/flags")
        data = resp.json["data"]

        platforms = [f["platform"] for f in data]
        assert "win" in platforms
        assert "nix" in platforms

    def test_api_flags_returns_all_permissions(self):
        """Test that flags with different permissions are returned"""
        user_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "C:\\test", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False,
        )
        root_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.root,
            data={"path": "C:\\admin", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False,
        )
        db.session.add_all([user_flag, root_flag])
        db.session.commit()

        self.login("reduser")
        resp = self.client.get("/api/flags")
        data = resp.json["data"]

        perms = [f["perm"] for f in data]
        assert "user" in perms
        assert "root" in perms

    # Solve Status Tests
    def test_api_flags_solves_with_no_solves(self):
        """Test that solves endpoint works with no solves"""
        service1 = Service(name="Host1", check_name="AgentCheck", host="192.168.1.10", team=self.blue_team1, port=0)
        service2 = Service(name="Host2", check_name="AgentCheck", host="192.168.1.20", team=self.blue_team2, port=0)
        db.session.add_all([service1, service2])
        db.session.commit()

        self.login("reduser")
        resp = self.client.get("/api/flags/solves")
        data = resp.json["data"]

        assert "columns" in data
        assert "rows" in data
        assert "Team" in data["columns"]

    def test_api_flags_solves_shows_solve_status(self):
        """Test that solve status is correctly shown"""
        service1 = Service(name="Host1", check_name="AgentCheck", host="192.168.1.10", team=self.blue_team1, port=0)
        service2 = Service(name="Host2", check_name="AgentCheck", host="192.168.1.20", team=self.blue_team2, port=0)

        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "C:\\test", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False,
        )
        db.session.add_all([service1, service2, flag])
        db.session.flush()

        solve = Solve(host="192.168.1.10", team_id=self.blue_team1.id, flag_id=flag.id)
        db.session.add(solve)
        db.session.commit()

        self.login("reduser")
        resp = self.client.get("/api/flags/solves")
        data = resp.json["data"]

        assert len(data["rows"]) >= 1

    # Totals Tests (Complex SQL)
    @pytest.mark.skip(reason="Requires MySQL - uses MySQL-specific IF() function")
    def test_api_flags_totals_empty(self):
        """Test totals with no flags or solves"""
        self.login("reduser")
        resp = self.client.get("/api/flags/totals")
        data = resp.json["data"]

        team_names = [entry["team"] for entry in data]
        assert "Blue Team 1" in team_names
        assert "Blue Team 2" in team_names

        for entry in data:
            assert entry["win_score"] == 0
            assert entry["nix_score"] == 0
            assert entry["total_score"] == 0

    @pytest.mark.skip(reason="Requires MySQL - uses MySQL-specific IF() function")
    def test_api_flags_totals_user_level_scoring(self):
        """Test that user-level flags count as 0.5"""
        service = Service(name="Host1", check_name="AgentCheck", host="192.168.1.10", team=self.blue_team1, port=0)
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "C:\\test", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False,
        )
        solve = Solve(host="192.168.1.10", team_id=self.blue_team1.id, flag_id=flag.id)
        db.session.add_all([service, flag, solve])
        db.session.commit()

        self.login("reduser")
        resp = self.client.get("/api/flags/totals")
        data = resp.json["data"]

        team1_entry = next(e for e in data if e["team"] == "Blue Team 1")
        assert team1_entry["win_score"] == 0.5
        assert team1_entry["nix_score"] == 0
        assert team1_entry["total_score"] == 0.5

    @pytest.mark.skip(reason="Requires MySQL - uses MySQL-specific IF() function")
    def test_api_flags_totals_root_level_scoring(self):
        """Test that root-level flags count as 1"""
        service = Service(name="Host1", check_name="AgentCheck", host="192.168.1.10", team=self.blue_team1, port=0)
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            perm=Perm.root,
            data={"path": "/etc/test", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False,
        )
        solve = Solve(host="192.168.1.10", team_id=self.blue_team1.id, flag_id=flag.id)
        db.session.add_all([service, flag, solve])
        db.session.commit()

        self.login("reduser")
        resp = self.client.get("/api/flags/totals")
        data = resp.json["data"]

        team1_entry = next(e for e in data if e["team"] == "Blue Team 1")
        assert team1_entry["nix_score"] == 1
        assert team1_entry["win_score"] == 0
        assert team1_entry["total_score"] == 1

    @pytest.mark.skip(reason="Requires MySQL - uses MySQL-specific IF() function")
    def test_api_flags_totals_user_and_root_scoring(self):
        """Test that user + root on same host counts as root (1.0)"""
        service = Service(name="Host1", check_name="AgentCheck", host="192.168.1.10", team=self.blue_team1, port=0)
        user_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "C:\\user", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False,
        )
        root_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.root,
            data={"path": "C:\\admin", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False,
        )
        solve_user = Solve(host="192.168.1.10", team_id=self.blue_team1.id, flag_id=user_flag.id)
        solve_root = Solve(host="192.168.1.10", team_id=self.blue_team1.id, flag_id=root_flag.id)
        db.session.add_all([service, user_flag, root_flag, solve_user, solve_root])
        db.session.commit()

        self.login("reduser")
        resp = self.client.get("/api/flags/totals")
        data = resp.json["data"]

        team1_entry = next(e for e in data if e["team"] == "Blue Team 1")
        assert team1_entry["win_score"] == 1
        assert team1_entry["total_score"] == 1

    @pytest.mark.skip(reason="Requires MySQL - uses MySQL-specific IF() function")
    def test_api_flags_totals_multiple_hosts(self):
        """Test scoring across multiple hosts"""
        service1 = Service(name="Host1", check_name="AgentCheck", host="192.168.1.10", team=self.blue_team1, port=0)
        service2 = Service(name="Host2", check_name="AgentCheck", host="192.168.1.20", team=self.blue_team1, port=0)
        flag1 = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.root,
            data={"path": "C:\\test1", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False,
        )
        flag2 = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.root,
            data={"path": "C:\\test2", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False,
        )
        solve1 = Solve(host="192.168.1.10", team_id=self.blue_team1.id, flag_id=flag1.id)
        solve2 = Solve(host="192.168.1.20", team_id=self.blue_team1.id, flag_id=flag2.id)
        db.session.add_all([service1, service2, flag1, flag2, solve1, solve2])
        db.session.commit()

        self.login("reduser")
        resp = self.client.get("/api/flags/totals")
        data = resp.json["data"]

        team1_entry = next(e for e in data if e["team"] == "Blue Team 1")
        assert team1_entry["win_score"] == 2
        assert team1_entry["total_score"] == 2

    @pytest.mark.skip(reason="Requires MySQL - uses MySQL-specific IF() function")
    def test_api_flags_totals_mixed_platforms(self):
        """Test scoring with both Windows and Linux flags"""
        service = Service(name="Host1", check_name="AgentCheck", host="192.168.1.10", team=self.blue_team1, port=0)
        win_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.root,
            data={"path": "C:\\test", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False,
        )
        nix_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            perm=Perm.root,
            data={"path": "/etc/test", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False,
        )
        solve_win = Solve(host="192.168.1.10", team_id=self.blue_team1.id, flag_id=win_flag.id)
        solve_nix = Solve(host="192.168.1.10", team_id=self.blue_team1.id, flag_id=nix_flag.id)
        db.session.add_all([service, win_flag, nix_flag, solve_win, solve_nix])
        db.session.commit()

        self.login("reduser")
        resp = self.client.get("/api/flags/totals")
        data = resp.json["data"]

        team1_entry = next(e for e in data if e["team"] == "Blue Team 1")
        assert team1_entry["win_score"] == 1
        assert team1_entry["nix_score"] == 1
        assert team1_entry["total_score"] == 2

    @pytest.mark.skip(reason="Requires MySQL - uses MySQL-specific IF() function")
    def test_api_flags_totals_multiple_teams(self):
        """Test that each team's score is calculated independently"""
        service1 = Service(name="Host1", check_name="AgentCheck", host="192.168.1.10", team=self.blue_team1, port=0)
        service2 = Service(name="Host2", check_name="AgentCheck", host="192.168.1.20", team=self.blue_team2, port=0)
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.root,
            data={"path": "C:\\test", "content": "test"},
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            dummy=False,
        )
        solve1 = Solve(host="192.168.1.10", team_id=self.blue_team1.id, flag_id=flag.id)
        db.session.add_all([service1, service2, flag, solve1])
        db.session.commit()

        self.login("reduser")
        resp = self.client.get("/api/flags/totals")
        data = resp.json["data"]

        team1_entry = next(e for e in data if e["team"] == "Blue Team 1")
        team2_entry = next(e for e in data if e["team"] == "Blue Team 2")
        assert team1_entry["total_score"] == 1
        assert team2_entry["total_score"] == 0
