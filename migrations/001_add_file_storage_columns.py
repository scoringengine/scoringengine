"""Migration: Add file storage support for comments and check outputs.

This migration adds columns to support storing large comments and check outputs
in files instead of truncating them in the database.

Usage:
    python migrations/001_add_file_storage_columns.py
"""

from sqlalchemy import create_engine, text
from scoring_engine.config import config


def migrate():
    """Run the migration to add file storage columns."""
    # Create database engine
    engine = create_engine(config.db_uri)

    with engine.connect() as conn:
        print("Starting migration: Add file storage columns...")

        # Add columns to comment table
        print("  - Adding file_path column to comment table...")
        conn.execute(text("ALTER TABLE comment ADD COLUMN file_path TEXT NULL"))

        print("  - Adding preview column to comment table...")
        conn.execute(text("ALTER TABLE comment ADD COLUMN preview TEXT NULL"))

        # Add column to checks table
        print("  - Adding output_file_path column to checks table...")
        conn.execute(text("ALTER TABLE checks ADD COLUMN output_file_path TEXT NULL"))

        # Create indexes
        print("  - Creating indexes for better query performance...")
        conn.execute(text("CREATE INDEX idx_comment_file_path ON comment(file_path)"))
        conn.execute(text("CREATE INDEX idx_checks_output_file_path ON checks(output_file_path)"))

        conn.commit()

        print("Migration completed successfully!")


def rollback():
    """Rollback the migration (remove added columns)."""
    engine = create_engine(config.db_uri)

    with engine.connect() as conn:
        print("Rolling back migration: Remove file storage columns...")

        # Drop indexes
        print("  - Dropping indexes...")
        conn.execute(text("DROP INDEX IF EXISTS idx_comment_file_path"))
        conn.execute(text("DROP INDEX IF EXISTS idx_checks_output_file_path"))

        # Drop columns from comment table
        print("  - Removing file_path column from comment table...")
        conn.execute(text("ALTER TABLE comment DROP COLUMN file_path"))

        print("  - Removing preview column from comment table...")
        conn.execute(text("ALTER TABLE comment DROP COLUMN preview"))

        # Drop column from checks table
        print("  - Removing output_file_path column from checks table...")
        conn.execute(text("ALTER TABLE checks DROP COLUMN output_file_path"))

        conn.commit()

        print("Rollback completed successfully!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback()
    else:
        migrate()
