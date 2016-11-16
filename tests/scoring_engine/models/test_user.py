import bcrypt

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.db import db_salt
from scoring_engine.models.user import User

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from helpers import generate_sample_model_tree

from .model_test import ModelTest


class TestUser(ModelTest):

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
