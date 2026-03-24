from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError, ProgrammingError

# Initialize Flask-SQLAlchemy
# This will be configured by the Flask app
db = SQLAlchemy()


def delete_db():
    """Drop all database tables"""
    dialect = db.engine.dialect.name
    with db.engine.connect() as conn:
        if dialect == "mysql":
            conn.execute(db.text("SET FOREIGN_KEY_CHECKS = 0"))
        elif dialect == "sqlite":
            conn.execute(db.text("PRAGMA foreign_keys = OFF"))
        conn.commit()
    db.drop_all()
    with db.engine.connect() as conn:
        if dialect == "mysql":
            conn.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        elif dialect == "sqlite":
            conn.execute(db.text("PRAGMA foreign_keys = ON"))
        conn.commit()


def init_db():
    """Create all database tables and stamp Alembic to head revision."""
    db.create_all()
    stamp_alembic_head()


def stamp_alembic_head():
    """Mark the database as being at the latest Alembic revision.

    Called after ``create_all()`` so that fresh databases start with the
    full migration history already applied (no need to run upgrades).
    """
    import os

    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "..", "alembic"))
    command.stamp(alembic_cfg, "head")


def run_migrations():
    """Run any pending Alembic migrations to bring the schema up to date."""
    import os

    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "..", "alembic"))
    command.upgrade(alembic_cfg, "head")


def verify_db_ready():
    """Verify the database is ready and accessible"""
    ready = True
    try:
        from scoring_engine.models.user import User

        db.session.get(User, 1)
    except (OperationalError, ProgrammingError):
        ready = False
    return ready
