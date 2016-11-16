from scoring_engine.db import db


class UnitTest(object):
    def setup(self):
        self.db = db
        self.db.connect()
        self.db.setup()

    def teardown(self):
        self.db.destroy()
