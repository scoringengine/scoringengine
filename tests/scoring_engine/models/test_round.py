import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../scoring_engine'))

from models.round import Round
from models.check import Check
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

    def test_init_round(self):
        round_obj = Round(number=5)
        assert round_obj.id is None
        assert round_obj.number == 5

    def test_basic_round(self):
        round_obj = Round(number=5)
        self.db.save(round_obj)
        assert round_obj.id is not None
        assert round_obj.number == 5

    def test_checks(self):
        service = generate_sample_model_tree('Service', self.db)
        round_obj = Round(number=5)
        self.db.save(round_obj)
        check_1 = Check(round=round_obj, service=service)
        self.db.save(check_1)
        check_2 = Check(round=round_obj, service=service)
        self.db.save(check_2)
        check_3 = Check(round=round_obj, service=service)
        self.db.save(check_3)
        assert round_obj.checks == [check_1, check_2, check_3]
