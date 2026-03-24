"""Alembic environment configuration.

Uses the Flask application context so migrations share the same DB URI
and SQLAlchemy metadata as the rest of the scoring engine.
"""

import sys
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool

# Ensure the project root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scoring_engine.web import create_app
from scoring_engine.db import db

# Interpret the config file for Python logging.
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models so metadata is fully populated
import scoring_engine.models  # noqa: F401

target_metadata = db.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode — emit SQL to stdout."""
    from scoring_engine.config import config as app_config

    context.configure(
        url=app_config.db_uri,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations inside the Flask app context."""
    app = create_app()
    with app.app_context():
        connectable = db.engine

        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
            )
            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
