from sqlalchemy.orm import scoped_session

from tests.scoring_engine.unit_test import UnitTest


class TestDB(UnitTest):

    def test_session_type(self):
        assert isinstance(self.session, scoped_session)
