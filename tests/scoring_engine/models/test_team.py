import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../scoring_engine'))

from models.team import Team
from db import DB


class TestTeam(object):
    def setup(self):
        self.db = DB()
        self.db.connect()
        self.db.setup()

    def teardown(self):
        self.db.destroy()

    def test_init_whiteteam(self):
        team = Team(name="White Team", color="White")
        assert team.name == "White Team"
        assert team.color == "White"
        assert team.id is None

    def test_init_blueteam(self):
        team = Team(name="Blue Team", color="Blue")
        assert team.name == "Blue Team"
        assert team.color == "Blue"
        assert team.id is None

    def test_init_redteam(self):
        team = Team(name="Red Team", color="Red")
        assert team.name == "Red Team"
        assert team.color == "Red"
        assert team.id is None

    def test_simple_save(self):
        white_team = Team(name="White Team", color="White")
        self.db.save(white_team)
        assert white_team.id is not None
        assert len(self.db.session.query(Team).all()) == 1

    def test_multiple_saves(self):
        white_team = Team(name="White Team", color="White")
        self.db.save(white_team)
        blue_team = Team(name="Blue", color="Blue")
        self.db.save(blue_team)
        assert len(self.db.session.query(Team).all()) == 2
