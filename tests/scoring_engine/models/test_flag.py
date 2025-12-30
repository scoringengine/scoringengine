import pytest
from datetime import datetime, timedelta
import pytz

from scoring_engine.models.flag import Flag, Solve, FlagTypeEnum, Platform, Perm
from scoring_engine.models.team import Team

from tests.scoring_engine.unit_test import UnitTest


class TestFlag(UnitTest):

    def test_init_file_flag(self):
        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            data={"path": "/root/flag.txt", "content": "flag{test123}"},
            start_time=start_time,
            end_time=end_time,
            perm=Perm.root,
            dummy=False
        )
        assert flag.type == FlagTypeEnum.file
        assert flag.platform == Platform.nix
        assert flag.data == {"path": "/root/flag.txt", "content": "flag{test123}"}
        assert flag.start_time == start_time
        assert flag.end_time == end_time
        assert flag.perm == Perm.root
        assert flag.dummy is False

    def test_init_pipe_flag(self):
        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        flag = Flag(
            type=FlagTypeEnum.pipe,
            platform=Platform.windows,
            data={"name": "flagpipe", "content": "flag{pipe123}"},
            start_time=start_time,
            end_time=end_time,
            perm=Perm.user,
            dummy=False
        )
        assert flag.type == FlagTypeEnum.pipe
        assert flag.platform == Platform.windows
        assert flag.perm == Perm.user

    def test_init_net_flag(self):
        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        flag = Flag(
            type=FlagTypeEnum.net,
            platform=Platform.nix,
            data={"port": 8080, "content": "flag{net123}"},
            start_time=start_time,
            end_time=end_time,
            perm=Perm.root,
            dummy=False
        )
        assert flag.type == FlagTypeEnum.net
        assert flag.data["port"] == 8080

    def test_init_reg_flag(self):
        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        flag = Flag(
            type=FlagTypeEnum.reg,
            platform=Platform.windows,
            data={"key": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Flag", "value": "flag{reg123}"},
            start_time=start_time,
            end_time=end_time,
            perm=Perm.root,
            dummy=False
        )
        assert flag.type == FlagTypeEnum.reg
        assert flag.platform == Platform.windows

    def test_dummy_flag(self):
        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            data={"path": "/tmp/dummy.txt"},
            start_time=start_time,
            end_time=end_time,
            perm=Perm.user,
            dummy=True
        )
        assert flag.dummy is True

    def test_simple_save(self):
        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            data={"path": "/root/flag.txt"},
            start_time=start_time,
            end_time=end_time,
            perm=Perm.root,
            dummy=False
        )
        self.session.add(flag)
        self.session.commit()
        assert flag.id is not None
        assert len(self.session.query(Flag).all()) == 1

    def test_as_dict(self):
        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            data={"path": "/root/flag.txt", "content": "flag{test123}"},
            start_time=start_time,
            end_time=end_time,
            perm=Perm.root,
            dummy=False
        )
        self.session.add(flag)
        self.session.commit()

        flag_dict = flag.as_dict()
        assert "id" in flag_dict
        assert flag_dict["type"] == "file"
        assert flag_dict["platform"] == "nix"
        assert flag_dict["data"] == {"path": "/root/flag.txt", "content": "flag{test123}"}
        assert flag_dict["start_time"] == int(start_time.timestamp())
        assert flag_dict["end_time"] == int(end_time.timestamp())
        assert flag_dict["perm"] == "root"
        assert flag_dict["dummy"] is False

    def test_as_dict_all_enums(self):
        """Test as_dict serialization for all enum combinations"""
        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)

        # Test with different enum combinations
        flag = Flag(
            type=FlagTypeEnum.net,
            platform=Platform.windows,
            data={"port": 9999},
            start_time=start_time,
            end_time=end_time,
            perm=Perm.user,
            dummy=True
        )
        self.session.add(flag)
        self.session.commit()

        flag_dict = flag.as_dict()
        assert flag_dict["type"] == "net"
        assert flag_dict["platform"] == "win"
        assert flag_dict["perm"] == "user"
        assert flag_dict["dummy"] is True

    def test_localize_start_time(self):
        """Test that start_time is properly localized to configured timezone"""
        start_time = datetime(2025, 1, 1, 12, 0, 0)  # Naive datetime (UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0)
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            data={"path": "/test"},
            start_time=start_time,
            end_time=end_time,
            perm=Perm.root,
            dummy=False
        )
        self.session.add(flag)
        self.session.commit()

        localized = flag.localize_start_time
        # Should be a string in format "YYYY-MM-DD HH:MM:SS TZ"
        assert isinstance(localized, str)
        assert "2025-01-01" in localized
        # Should contain timezone abbreviation
        assert any(tz in localized for tz in ["UTC", "EST", "PST", "MST", "CST"])

    def test_localize_end_time(self):
        """Test that end_time is properly localized to configured timezone"""
        start_time = datetime(2025, 1, 1, 12, 0, 0)
        end_time = datetime(2025, 1, 1, 18, 0, 0)
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            data={"path": "/test"},
            start_time=start_time,
            end_time=end_time,
            perm=Perm.root,
            dummy=False
        )
        self.session.add(flag)
        self.session.commit()

        localized = flag.localize_end_time
        # Should be a string in format "YYYY-MM-DD HH:MM:SS TZ"
        assert isinstance(localized, str)
        assert "2025-01-01" in localized
        assert any(tz in localized for tz in ["UTC", "EST", "PST", "MST", "CST"])


class TestSolve(UnitTest):

    def test_init(self):
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            data={"path": "/root/flag.txt"},
            start_time=start_time,
            end_time=end_time,
            perm=Perm.root,
            dummy=False
        )
        self.session.add(flag)
        self.session.commit()

        solve = Solve(host="10.0.0.1", flag=flag, team=team)
        self.session.add(solve)
        self.session.commit()

        assert solve.id is not None
        assert solve.host == "10.0.0.1"
        assert solve.flag_id == flag.id
        assert solve.team_id == team.id

    def test_solve_relationship_to_flag(self):
        """Test that Solve has proper relationship to Flag"""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            data={"path": "/root/flag.txt"},
            start_time=start_time,
            end_time=end_time,
            perm=Perm.root,
            dummy=False
        )
        self.session.add(flag)
        self.session.commit()

        solve = Solve(host="10.0.0.1", flag=flag, team=team)
        self.session.add(solve)
        self.session.commit()

        # Access solve through flag relationship
        assert len(flag.solves) == 1
        assert flag.solves[0].host == "10.0.0.1"

    def test_solve_relationship_to_team(self):
        """Test that Solve has proper relationship to Team"""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            data={"path": "/root/flag.txt"},
            start_time=start_time,
            end_time=end_time,
            perm=Perm.root,
            dummy=False
        )
        self.session.add(flag)
        self.session.commit()

        solve = Solve(host="10.0.0.1", flag=flag, team=team)
        self.session.add(solve)
        self.session.commit()

        # Access solve through team relationship
        assert len(team.flag_solves) == 1
        assert team.flag_solves[0].host == "10.0.0.1"

    def test_unique_constraint(self):
        """Test that the unique constraint on (flag_id, host, team_id) works"""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            data={"path": "/root/flag.txt"},
            start_time=start_time,
            end_time=end_time,
            perm=Perm.root,
            dummy=False
        )
        self.session.add(flag)
        self.session.commit()

        # Create first solve
        solve1 = Solve(host="10.0.0.1", flag=flag, team=team)
        self.session.add(solve1)
        self.session.commit()

        # Try to create duplicate solve with same flag, host, and team
        solve2 = Solve(host="10.0.0.1", flag=flag, team=team)
        self.session.add(solve2)

        # Should raise IntegrityError due to unique constraint
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            self.session.commit()

    def test_multiple_solves_different_hosts(self):
        """Test that same flag can be solved from different hosts"""
        team = Team(name="Blue Team 1", color="Blue")
        self.session.add(team)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            data={"path": "/root/flag.txt"},
            start_time=start_time,
            end_time=end_time,
            perm=Perm.root,
            dummy=False
        )
        self.session.add(flag)
        self.session.commit()

        solve1 = Solve(host="10.0.0.1", flag=flag, team=team)
        solve2 = Solve(host="10.0.0.2", flag=flag, team=team)
        self.session.add(solve1)
        self.session.add(solve2)
        self.session.commit()

        assert len(flag.solves) == 2

    def test_multiple_solves_different_teams(self):
        """Test that same flag can be solved by different teams"""
        team1 = Team(name="Blue Team 1", color="Blue")
        team2 = Team(name="Blue Team 2", color="Blue")
        self.session.add(team1)
        self.session.add(team2)

        start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=pytz.UTC)
        flag = Flag(
            type=FlagTypeEnum.file,
            platform=Platform.nix,
            data={"path": "/root/flag.txt"},
            start_time=start_time,
            end_time=end_time,
            perm=Perm.root,
            dummy=False
        )
        self.session.add(flag)
        self.session.commit()

        solve1 = Solve(host="10.0.0.1", flag=flag, team=team1)
        solve2 = Solve(host="10.0.0.1", flag=flag, team=team2)
        self.session.add(solve1)
        self.session.add(solve2)
        self.session.commit()

        assert len(flag.solves) == 2
        assert len(team1.flag_solves) == 1
        assert len(team2.flag_solves) == 1
