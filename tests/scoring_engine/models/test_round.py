import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.models.check import Check
from scoring_engine.models.round import Round

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
from helpers import generate_sample_model_tree
from unit_test import UnitTest


class TestRound(UnitTest):

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

    def test_get_last_round_num_rounds_exist(self):
        service = generate_sample_model_tree('Service', self.db)
        round_5 = Round(number=5)
        self.db.save(round_5)
        round_6 = Round(number=6)
        self.db.save(round_6)
        assert Round.get_last_round_num() == 6

    def test_get_last_round_num_non_exist(self):
        assert Round.get_last_round_num() == 0
