import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../scoring_engine'))

from models.team import Team
from models.server import Server
from models.user import User
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

    def test_servers(self):
        team = Team(name="Blue", color="Blue")
        self.db.save(team)
        server_1 = Server(name="Test Service 1", team=team)
        server_2 = Server(name="Test Service 2", team=team)
        self.db.save(server_1)
        self.db.save(server_2)
        assert team.servers == [server_1, server_2]

    def test_users(self):
        team = Team(name="Blue", color="Blue")
        self.db.save(team)
        user_1 = User(username="testuser", password="testpass", team=team)
        user_2 = User(username="abcuser", password="abcpass", team=team)
        self.db.save(user_1)
        self.db.save(user_2)
        assert team.users == [user_1, user_2]
