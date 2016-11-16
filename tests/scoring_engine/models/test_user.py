import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.db import db, db_salt
# from models.user import User
from scoring_engine.models.user import User
# from models.team import Team
# from db import DB

import bcrypt

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from helpers import generate_sample_model_tree


class TestUser(object):
    def setup(self):
        self.db = db
        self.db.connect()
        self.db.setup()

    def teardown(self):
        self.db.destroy()

    def test_init_service(self):
        user = User(username="testuser", password="testpass")
        assert user.id is None
        assert user.username == "testuser"
        assert user.password == bcrypt.hashpw("testpass".encode('utf-8'), db_salt)
        assert user.team is None
        assert user.team_id is None

    def test_basic_user(self):
        team = generate_sample_model_tree('Team', self.db)
        user = User(username="testuser", password="testpass", team=team)
        self.db.save(user)
        assert user.id is not None
        assert user.username == "testuser"
        assert user.password == bcrypt.hashpw("testpass".encode('utf-8'), db_salt)
        assert user.team is team
        assert user.team_id is team.id
