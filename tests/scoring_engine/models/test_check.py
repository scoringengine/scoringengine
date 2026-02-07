from scoring_engine.db import db
from scoring_engine.models.check import Check
from scoring_engine.models.round import Round
from tests.scoring_engine.helpers import generate_sample_model_tree


class TestCheck:

    def test_init_check(self):
        check = Check()
        assert check.id is None
        assert check.round is None
        assert check.round_id is None

    def test_basic_check(self):
        service = generate_sample_model_tree("Service", db.session)
        round_obj = Round(number=1)
        db.session.add(round_obj)
        check = Check(round=round_obj, service=service, result=True, output="example_output")
        db.session.add(check)
        db.session.commit()
        assert check.id is not None
        assert check.round == round_obj
        assert check.round_id == round_obj.id
        assert check.service == service
        assert check.service_id == service.id
        assert check.result is True
        assert check.output == "example_output"
        assert check.completed is False

    def test_finished(self):
        service = generate_sample_model_tree("Service", db.session)
        round_obj = Round(number=1)
        db.session.add(round_obj)
        check = Check(round=round_obj, service=service)
        db.session.add(check)
        db.session.commit()
        assert check.result is None
        assert check.output == ""
        assert check.completed is False
        assert check.reason == ""
        check.finished(True, "Successful Match", "good output", "example command")
        db.session.add(check)
        db.session.commit()
        assert check.result is True
        assert check.output == "good output"
        assert check.reason == "Successful Match"
        assert check.command == "example command"
        assert check.completed is True
        assert type(check.local_completed_timestamp) is str
