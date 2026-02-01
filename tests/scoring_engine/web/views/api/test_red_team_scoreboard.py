import json
from datetime import datetime, timedelta

from scoring_engine.models.flag import Flag, FlagTypeEnum, Perm, Platform, Solve
from scoring_engine.models.team import Team
from scoring_engine.web import create_app
from tests.scoring_engine.unit_test import UnitTest


class TestRedTeamScoreboard(UnitTest):
    def setup_method(self):
        super(TestRedTeamScoreboard, self).setup_method()
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def teardown_method(self):
        self.ctx.pop()
        super(TestRedTeamScoreboard, self).teardown_method()

    def test_get_red_team_data_no_captures(self):
        """Test endpoint returns empty captures when no flags exist."""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)
        self.session.commit()

        resp = self.client.get("/api/scoreboard/get_red_team_data")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["total_captures"] == 0
        assert data["total_red_points"] == 0.0
        assert len(data["captures"]) == 1
        assert data["captures"][0]["team"] == "Blue Team 1"
        assert data["captures"][0]["total_score"] == 0.0

    def test_get_red_team_data_with_nix_root_capture(self):
        """Test scoring for nix root capture (1.0 points)."""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)
        self.session.commit()

        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            perm=Perm.root,
            data={"path": "/tmp/flag.txt"},
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=1),
            dummy=False,
        )
        self.session.add(flag)
        self.session.commit()

        solve = Solve(flag=flag, host="test.host", team_id=team.id)
        self.session.add(solve)
        self.session.commit()

        resp = self.client.get("/api/scoreboard/get_red_team_data")
        data = json.loads(resp.data)

        assert data["total_captures"] == 1
        assert data["total_red_points"] == 1.0

        team1_data = next((c for c in data["captures"] if c["team"] == "Blue Team 1"), None)
        assert team1_data is not None
        assert team1_data["nix_root"] == 1
        assert team1_data["nix_score"] == 1.0
        assert team1_data["total_score"] == 1.0

    def test_get_red_team_data_with_windows_user_capture(self):
        """Test scoring for windows user capture (0.5 points)."""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)
        self.session.commit()

        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "C:\\flag.txt"},
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=1),
            dummy=False,
        )
        self.session.add(flag)
        self.session.commit()

        solve = Solve(flag=flag, host="test.host", team_id=team.id)
        self.session.add(solve)
        self.session.commit()

        resp = self.client.get("/api/scoreboard/get_red_team_data")
        data = json.loads(resp.data)

        assert data["total_captures"] == 1
        assert data["total_red_points"] == 0.5

        team1_data = next((c for c in data["captures"] if c["team"] == "Blue Team 1"), None)
        assert team1_data is not None
        assert team1_data["windows_user"] == 1
        assert team1_data["windows_score"] == 0.5
        assert team1_data["total_score"] == 0.5

    def test_get_red_team_data_excludes_dummy_flags(self):
        """Test that dummy flags are not counted in captures."""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)
        self.session.commit()

        # Create a dummy flag (should be excluded)
        dummy_flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            perm=Perm.root,
            data={"path": "/tmp/dummy.txt"},
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=1),
            dummy=True,
        )
        self.session.add(dummy_flag)
        self.session.commit()

        solve = Solve(flag=dummy_flag, host="test.host", team_id=team.id)
        self.session.add(solve)
        self.session.commit()

        resp = self.client.get("/api/scoreboard/get_red_team_data")
        data = json.loads(resp.data)

        assert data["total_captures"] == 0
        assert data["total_red_points"] == 0.0

    def test_get_red_team_data_multiple_teams_and_captures(self):
        """Test aggregation across multiple teams and capture types."""
        team1 = Team(name="Blue Team 1", color="Blue")
        team2 = Team(name="Blue Team 2", color="Blue")
        self.session.add_all([team1, team2])
        self.session.commit()

        # Team 1: nix root (1.0) + windows user (0.5) = 1.5
        flag1 = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            perm=Perm.root,
            data={"path": "/tmp/flag1.txt"},
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=1),
            dummy=False,
        )
        flag2 = Flag(
            type=FlagTypeEnum.pipe,
            platform=Platform.windows,
            perm=Perm.user,
            data={"path": "C:\\flag2.txt"},
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=1),
            dummy=False,
        )
        # Team 2: windows root (1.0)
        flag3 = Flag(
            type=FlagTypeEnum.reg,
            platform=Platform.windows,
            perm=Perm.root,
            data={"path": "HKLM\\flag3"},
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=1),
            dummy=False,
        )
        self.session.add_all([flag1, flag2, flag3])
        self.session.commit()

        solve1 = Solve(flag=flag1, host="host1.team1", team_id=team1.id)
        solve2 = Solve(flag=flag2, host="host2.team1", team_id=team1.id)
        solve3 = Solve(flag=flag3, host="host1.team2", team_id=team2.id)
        self.session.add_all([solve1, solve2, solve3])
        self.session.commit()

        resp = self.client.get("/api/scoreboard/get_red_team_data")
        data = json.loads(resp.data)

        assert data["total_captures"] == 3
        assert data["total_red_points"] == 2.5  # 1.0 + 0.5 + 1.0

        team1_data = next((c for c in data["captures"] if c["team"] == "Blue Team 1"), None)
        assert team1_data["nix_root"] == 1
        assert team1_data["nix_score"] == 1.0
        assert team1_data["windows_user"] == 1
        assert team1_data["windows_score"] == 0.5
        assert team1_data["total_captures"] == 2
        assert team1_data["total_score"] == 1.5

        team2_data = next((c for c in data["captures"] if c["team"] == "Blue Team 2"), None)
        assert team2_data["windows_root"] == 1
        assert team2_data["windows_score"] == 1.0
        assert team2_data["total_captures"] == 1
        assert team2_data["total_score"] == 1.0
