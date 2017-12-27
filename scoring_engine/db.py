import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from scoring_engine.config import config


isolation_level = "READ COMMITTED"
if 'sqlite' in config.db_uri:
    # sqlite db does not support transaction based statements
    # so we have to manually set it to something else
    isolation_level = "READ UNCOMMITTED"

engine = create_engine(config.db_uri, isolation_level=isolation_level)

session = scoped_session(sessionmaker(bind=engine))

db_salt = bcrypt.gensalt()


# This is a monkey patch so that we
# don't need to commit before every query
# We got weird results in the web ui when we didn't
# have this
def query_monkeypatch(classname):
    session.commit()
    return session.orig_query(classname)


session.orig_query = session.query
session.query = query_monkeypatch
