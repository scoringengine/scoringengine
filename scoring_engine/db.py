import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from scoring_engine.engine.config import config


engine = create_engine(config.db_uri, isolation_level="READ UNCOMMITTED")

session = scoped_session(sessionmaker(bind=engine))

db_salt = bcrypt.gensalt()
