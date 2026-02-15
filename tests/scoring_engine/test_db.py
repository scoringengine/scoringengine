from sqlalchemy.orm import scoped_session

from scoring_engine.db import db


class TestDB:

    def test_session_type(self):
        assert isinstance(db.session, scoped_session)
