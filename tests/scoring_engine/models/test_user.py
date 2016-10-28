import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../scoring_engine'))

from models.user import User
from models.check import Check
from models.service import Service
from models.server import Server
from models.team import Team
from db import DB

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from helpers import generate_sample_model_tree


class TestUser(object):
    def setup(self):
        self.db = DB()
        self.db.connect()
        self.db.setup()

    def teardown(self):
        self.db.destroy()

    def test_init_service(self):
        user = User(username="testuser", password="testpass")
        assert user.id is None
        assert user.username == "testuser"
        assert user.password == "testpass"
        assert user.team is None
        assert user.team_id is None

    def test_basic_user(self):
        team = generate_sample_model_tree('Team', self.db)
        user = User(username="testuser", password="testpass", team=team)
        self.db.save(user)
        assert user.id is not None
        assert user.username == "testuser"
        assert user.password == "testpass"
        assert user.team is team
        assert user.team_id is team.id
