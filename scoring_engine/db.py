import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from scoring_engine.web import app

from scoring_engine.db_not_connected import DBNotConnected


class DB(object):
    def __init__(self):
        self.connected = False
        self.sqlite_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../engine.db')

    def connect(self):
        self.connected = True
        self.engine = create_engine(app.config['DATABASE_URI'], convert_unicode=True, **app.config['DATABASE_CONNECT_OPTIONS'])
        self.session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=self.engine))

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


db = DB()
db.connect()


from scoring_engine.models.base import Base

