import os
import sys
from scoring_engine.db import DB


class UnitTest(object):
    def setup(self):
        self.db = DB(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_engine.db'))
        self.db.connect()
        self.db.setup()

    def teardown(self):
        self.db.destroy()
