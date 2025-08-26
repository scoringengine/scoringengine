from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError, ProgrammingError


db = SQLAlchemy()

# Maintain backward compatibility for modules importing `session`
session = db.session


def delete_db():
    from scoring_engine.models.base import Base

    Base.metadata.drop_all(bind=db.engine)


def init_db():
    from scoring_engine.models.base import Base

    Base.metadata.create_all(bind=db.engine)


def verify_db_ready():
    ready = True
    try:
        from scoring_engine.models.user import User

        db.session.get(User, 1)
    except (OperationalError, ProgrammingError):
        ready = False
    return ready

