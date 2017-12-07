from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import bcrypt

from scoring_engine.db_not_connected import DBNotConnected

from scoring_engine.engine.config import config

db_salt = bcrypt.gensalt()


class DB(object):
    def __init__(self):
        self.connected = False
        self.db_uri = config.db_uri

    def connect(self):
        self.connected = True
        self.engine = create_engine(
            self.db_uri,
            convert_unicode=True,
        )
        self.session = scoped_session(sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=True,
            expire_on_commit=True,
        ))

    def setup(self):
        if not self.connected:
            raise DBNotConnected()
        from scoring_engine.models.base import Base
        Base.metadata.create_all(self.engine)

    def destroy(self):
        if not self.connected:
            raise DBNotConnected()
        from scoring_engine.models.base import Base
        Base.metadata.drop_all(self.engine)

    def save(self, obj):
        self.connect()

        if not self.connected:
            raise DBNotConnected()

        try:
            self.session.add(obj)
            self.session.commit()
        except:
            self.session.rollback()
            raise
        finally:
            self.session.close()

    def disconnect(self):
        self.engine.dispose()
        self.session.close()


db = DB()
db.connect()
