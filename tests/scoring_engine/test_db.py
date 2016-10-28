from sqlalchemy.orm import Session
import pytest

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../scoring_engine'))

from db import DB
from db_not_connected import DBNotConnected
from models.team import Team


class TestDB(object):

    def setup(self):
        self.db = DB()

    def teardown(self):
        if os.path.isfile(self.db.sqlite_db):
            os.remove(self.db.sqlite_db)

    def test_init(self):
        assert self.db.connected is False
        assert os.path.isfile(self.db.sqlite_db) is False

    def test_connect_without_setup(self):
        self.db.connect()
        assert self.db.connected is True
        assert os.path.isfile(self.db.sqlite_db) is False
        assert isinstance(self.db.session, Session) is True

    def test_setup_without_connecting(self):
        with pytest.raises(DBNotConnected):
            self.db.setup()

    def test_connect_setup(self):
        self.db.connect()
        self.db.setup()
        assert os.path.isfile(self.db.sqlite_db) is True

    def test_destroy(self):
        self.db.connect()
        self.db.setup()
        assert os.path.isfile(self.db.sqlite_db) is True
        self.db.destroy()
        assert os.path.isfile(self.db.sqlite_db) is False

    def test_save_without_connecting(self):
        obj = Team(name="White Team", color="White")
        with pytest.raises(DBNotConnected):
            self.db.save(obj)
