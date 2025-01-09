import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.pool import NullPool

from scoring_engine.config import config


def delete_db(session):
    from scoring_engine.models.base import Base

    Base.metadata.drop_all(session.bind)


def init_db(session):
    from scoring_engine.models.base import Base

    Base.metadata.create_all(session.bind)


def verify_db_ready(session):
    ready = True
    try:
        from scoring_engine.models.user import User

        session.query(User).get(1)
    except (OperationalError, ProgrammingError):
        ready = False
    return ready


isolation_level = "READ COMMITTED"
if "sqlite" in config.db_uri:
    # sqlite db does not support transaction based statements
    # so we have to manually set it to something else
    isolation_level = "READ UNCOMMITTED"

session = scoped_session(
    sessionmaker(bind=create_engine(config.db_uri, isolation_level=isolation_level, poolclass=NullPool))
)

# db_salt = bcrypt.gensalt()


# This is a monkey patch so that we
# don't need to commit before every query
# We got weird results in the web ui when we didn't
# have this
def query_monkeypatch(*classname):
    session.commit()
    return session.orig_query(*classname)


session.orig_query = session.query
session.query = query_monkeypatch
