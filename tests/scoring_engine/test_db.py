from sqlalchemy.orm import scoped_session
from sqlalchemy.exc import OperationalError
import pytest

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from scoring_engine.db import DB
from scoring_engine.db_not_connected import DBNotConnected
from scoring_engine.models.team import Team


class TestDB(object):

    def setup(self):
        self.db = DB()
        try:
            self.db.destroy()
        except DBNotConnected:
            pass

    def teardown(self):
        try:
            self.db.destroy()
        except DBNotConnected:
            pass

    def test_init(self):
        assert self.db.connected is False

    def test_connect_without_setup(self):
        self.db.connect()
        assert self.db.connected is True
        assert isinstance(self.db.session, scoped_session) is True

    def test_setup_without_connecting(self):
        with pytest.raises(DBNotConnected):
            self.db.setup()

    def test_save_without_connecting(self):
        obj = Team(name="White Team", color="White")
        with pytest.raises(DBNotConnected):
            self.db.save(obj)

    def test_save_and_destroy(self):
        self.db.connect()
        self.db.setup()
        obj = Team(name="White Team", color="White")
        self.db.save(obj)
        assert len(Team.query.all()) == 1
        self.db.destroy()
        with pytest.raises(OperationalError):
            Team.query.all()
