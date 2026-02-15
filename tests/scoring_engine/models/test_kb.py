from scoring_engine.db import db
from scoring_engine.models.kb import KB


class TestKB:

    def test_init_property(self):
        kb = KB(name="task_ids", value="1,2,3,4,5,6", round_num=100)
        assert kb.id is None
        assert kb.name == "task_ids"
        assert kb.value == "1,2,3,4,5,6"
        assert kb.round_num == 100

    def test_basic_kb(self):
        kb = KB(name="task_ids", value="1,2,3,4,5,6", round_num=50)
        db.session.add(kb)
        db.session.commit()
        assert kb.id is not None
