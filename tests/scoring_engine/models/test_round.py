from scoring_engine.db import db
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from tests.scoring_engine.helpers import generate_sample_model_tree


class TestRound:

    def test_init_round(self):
        round_obj = Round(number=5)
        assert round_obj.id is None
        assert round_obj.number == 5

    def test_basic_round(self):
        round_obj = Round(number=5)
        db.session.add(round_obj)
        db.session.commit()
        assert round_obj.id is not None
        assert round_obj.number == 5
        assert type(round_obj.local_round_start) is str

    def test_checks(self):
        service = generate_sample_model_tree("Service", db.session)
        round_obj = Round(number=5)
        db.session.add(round_obj)
        check_1 = Check(round=round_obj, service=service)
        db.session.add(check_1)
        check_2 = Check(round=round_obj, service=service)
        db.session.add(check_2)
        check_3 = Check(round=round_obj, service=service)
        db.session.add(check_3)
        db.session.commit()
        assert round_obj.checks == [check_1, check_2, check_3]

    def test_get_last_round_num_rounds_exist(self):
        generate_sample_model_tree("Service", db.session)
        round_5 = Round(number=5)
        db.session.add(round_5)
        round_6 = Round(number=6)
        db.session.add(round_6)
        db.session.commit()
        assert Round.get_last_round_num() == 6

    def test_get_last_round_num_non_exist(self):
        assert Round.get_last_round_num() == 0
