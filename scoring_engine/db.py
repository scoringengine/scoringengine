import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import Config
from models.base import Base

from db_not_connected import DBNotConnected


class DB(object):
    def __init__(self):
        config = Config()
        print("Connecting to DB")
        print("\tHost: " + config.db_host)
        print("\tPort: " + config.db_host)
        print("\tUsername: " + config.db_host)
        print("\tPassword: " + config.db_host)
        self.connected = False
        self.sqlite_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../engine.db')

    def connect(self):
        self.connected = True
        self.db_engine = create_engine('sqlite:///' + self.sqlite_db)
        self.session = sessionmaker(bind=self.db_engine)()

    def setup(self):
        if not self.connected:
            raise DBNotConnected()
        self.destroy()
        Base.metadata.create_all(self.db_engine)

    def destroy(self):
        if os.path.isfile(self.sqlite_db):
            print("Deleting sqlite db file")
            os.remove(self.sqlite_db)

    def save(self, obj):
        if not self.connected:
            raise DBNotConnected()

        self.session.add(obj)
        self.session.commit()
