import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.exc import OperationalError, ProgrammingError, InterfaceError
from sqlalchemy.pool import NullPool

from scoring_engine.config import config
from scoring_engine.logger import db_logger

DB_CONNECTION_ERRORS = {
    "authentication": [
        "password authentication failed",
        "access denied",
        "login failed",
        "invalid password",
        "authentication failed",
    ],
    "unreachable": [
        "could not connect",
        "connection refused",
        "no route to host",
        "network is unreachable",
        "host is down",
        "connection timed out",
        "name or service not known",
        "unknown host",
        "getaddrinfo failed",
    ],
    "database_missing": [
        "database does not exist",
        "unknown database",
        "no such file or directory",
    ],
}

# Translate exceptions into readable error logs
def get_readable_error_message(exception):
    error_str = str(exception).lower()

    for error_type, patterns in DB_CONNECTION_ERRORS.items():
        for pattern in patterns:
            if pattern in error_str:
                if error_type == "authentication":
                    return (
                        "authentication",
                        "Database authentication failed - check username and password in DB_URI",
                    )
                elif error_type == "unreachable":
                    return (
                        "unreachable",
                        "Database host is unreachable - verify the host address is correct and the database server is running",
                    )
                elif error_type == "database_missing":
                    return (
                        "database_missing",
                        "Database does not exist - verify the database name in DB_URI or create the database",
                    )

    return ("unknown", f"Database error: {exception}")

def test_db_connection(db_uri: str = None) -> tuple[bool, str]:
    from sqlalchemy import create_engine, text
    
    uri = db_uri or config.db_uri
    
    try:
        test_engine = create_engine(uri, poolclass=NullPool)
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_logger.info("[DB] Connection test successful")
        return (True, "Connected")
    except (OperationalError, InterfaceError) as e:
        error_type, readable_msg = get_readable_error_message(e)
        db_logger.warning(f"[DB] Connection test failed: {readable_msg}")
        if error_type == "authentication":
            return (False, "Invalid password")
        elif error_type == "unreachable":
            return (False, "Host unreachable")
        elif error_type == "database_missing":
            return (False, "Database not found")
        return (False, f"{readable_msg}")
    except Exception as e:
        db_logger.warning(f"[DB] Connection test failed with unexpected error: {e}")
        return (False, f"Connection failed: {e}")

def delete_db():
    """Drop all database tables"""
    db.drop_all()

    try:
        Base.metadata.drop_all(session.bind)
        db_logger.info("[DB] Database tables dropped successfully")
    except (OperationalError, InterfaceError) as e:
        error_type, readable_msg = get_readable_error_message(e)
        db_logger.error(f"[DB DELETE ERROR] Failed to drop database tables: {readable_msg}")
        db_logger.error(f"  Details: {e}")
        raise
    except Exception as e:
        db_logger.error("[DB DELETE ERROR] Unexpected error while dropping database tables")
        db_logger.error(f"  Details: {e}")
        raise

def init_db():
    """Create all database tables"""
    db.create_all()


    try:
        Base.metadata.create_all(session.bind)
        db_logger.info("[DB] Database tables created successfully")
    except (OperationalError, InterfaceError) as e:
        error_type, readable_msg = get_readable_error_message(e)
        db_logger.error(f"[DB INIT ERROR] Failed to create database tables: {readable_msg}")
        db_logger.error(f"  Details: {e}")
        raise
    except Exception as e:
        db_logger.error("[DB INIT ERROR] Unexpected error while creating database tables")
        db_logger.error(f"  Details: {e}")
        raise


def verify_db_ready(session):
    ready = True
    try:
        from scoring_engine.models.user import User

        session.get(User, 1)
        db_logger.debug("[DB] Database readiness check passed")
    except (OperationalError, ProgrammingError) as e:
        error_type, readable_msg = get_readable_error_message(e)
        db_logger.warning(f"[DB CHECK] Database not ready: {readable_msg}")
        db_logger.debug(f"  Details: {e}")
        ready = False
    except Exception as e:
        db_logger.warning("[DB CHECK] Database readiness check failed with unexpected error")
        db_logger.debug(f"  Details: {e}")
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
