import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../scoring_engine'))

from models.team import Team
from models.server import Server
from models.service import Service
from models.check import Check
from db import DB

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from helpers import generate_sample_model_tree


class TestCheck(object):
    def setup(self):
        self.db = DB()
        self.db.connect()
        self.db.setup()

    def teardown(self):
        self.db.destroy()

    def test_init_check(self):
        check = Check()
        assert check.id is None
        assert check.round is None
        assert check.round_id is None

    def test_basic_check(self):
        round = generate_sample_model_tree('Round', self.db)
        check = Check(round=round)
        self.db.save(check)
        assert check.id is not None
        assert check.round == round
        assert check.round_id == round.id
