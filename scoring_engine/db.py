from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import bcrypt

from scoring_engine.db_not_connected import DBNotConnected

db_salt = bcrypt.gensalt()
from scoring_engine.engine.config import config


class DB(object):
    def __init__(self):
        self.connected = False
        self.db_uri = config.db_uri

    def connect(self):
        self.connected = True
        self.engine = create_engine(self.db_uri, convert_unicode=True)
        # self.session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=self.engine))
        self.session = scoped_session(sessionmaker(autocommit=False, bind=self.engine))

    def setup(self):
        if not self.connected:
            raise DBNotConnected()
        from scoring_engine.models.user import User
        from scoring_engine.models.team import Team
        from scoring_engine.models.service import Service
        from scoring_engine.models.check import Check
        from scoring_engine.models.property import Property
        from scoring_engine.models.round import Round
        from scoring_engine.models.kb import KB
        from scoring_engine.models.base import Base
        Base.metadata.create_all(self.engine)

    def destroy(self):
        if not self.connected:
            raise DBNotConnected()
        from scoring_engine.models.user import User
        from scoring_engine.models.team import Team
        from scoring_engine.models.service import Service
        from scoring_engine.models.check import Check
        from scoring_engine.models.property import Property
        from scoring_engine.models.round import Round
        from scoring_engine.models.kb import KB
        from scoring_engine.models.base import Base
        Base.metadata.drop_all(self.engine)

    def save(self, obj):
        if not self.connected:
            raise DBNotConnected()

        self.session.add(obj)
        self.session.commit()


db = DB()
db.connect()
