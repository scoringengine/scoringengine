import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../scoring_engine'))

from models.round import Round
from db import DB

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from helpers import generate_sample_model_tree


class TestRound(object):
    def setup(self):
        self.db = DB()
        self.db.connect()
        self.db.setup()

    def teardown(self):
        self.db.destroy()

    def test_init_property(self):
        round_obj = Round(number=5)
        assert round_obj.id is None
        assert round_obj.number == 5
