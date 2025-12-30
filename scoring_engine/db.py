from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError, ProgrammingError

# Initialize Flask-SQLAlchemy
# This will be configured by the Flask app
db = SQLAlchemy()


def delete_db():
    """Drop all database tables"""
    db.drop_all()


def init_db():
    """Create all database tables"""
    db.create_all()


def verify_db_ready():
    """Verify the database is ready and accessible"""
    ready = True
    try:
        from scoring_engine.models.user import User
        db.session.get(User, 1)
    except (OperationalError, ProgrammingError):
        ready = False
    return ready
