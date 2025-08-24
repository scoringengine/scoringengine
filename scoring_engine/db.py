from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.pool import NullPool

from scoring_engine.config import config


isolation_level = "READ COMMITTED"
if "sqlite" in config.db_uri:
    # sqlite db does not support transaction based statements
    # so we have to manually set it to something else
    isolation_level = "READ UNCOMMITTED"

db = SQLAlchemy(engine_options={"isolation_level": isolation_level, "poolclass": NullPool})
session = db.session


def delete_db(_session=None):
    """Drop all tables from the database."""
    db.drop_all()


def init_db(_session=None):
    """Create all tables in the database."""
    db.create_all()


def verify_db_ready(_session=None):
    """Return True if the database is initialized."""
    ready = True
    try:
        from scoring_engine.models.user import User

        db.session.query(User).get(1)
    except (OperationalError, ProgrammingError):
        ready = False
    return ready



