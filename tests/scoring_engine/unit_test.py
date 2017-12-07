from scoring_engine.db import session, engine
from scoring_engine.models.base import Base


class UnitTest(object):
    def setup(self):
        self.session = session
        Base.metadata.create_all(engine)

    def teardown(self):
        Base.metadata.drop_all(engine)
        self.session.close_all()
