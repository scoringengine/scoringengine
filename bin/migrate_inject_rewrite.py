#!/usr/bin/env python
"""
Migration script for the inject system rewrite.

Migrates existing databases from the old inject schema (single score,
comment/file tables) to the new schema (rubric-based scoring,
inject_comment/inject_file tables).

This script uses raw SQL (not ORM) since old schema won't match new models.
Safe to re-run (idempotent).

Usage:
    python bin/migrate_inject_rewrite.py
"""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scoring_engine.db import db, init_db
from scoring_engine.web import create_app
from scoring_engine.logger import logger


def table_exists(table_name):
    """Check if a table exists in the database."""
    result = db.session.execute(
        db.text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = :name"),
        {"name": table_name},
    )
    return result.scalar() > 0


def column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    result = db.session.execute(
        db.text(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_name = :table AND column_name = :column"
        ),
        {"table": table_name, "column": column_name},
    )
    return result.scalar() > 0


def migrate():
    app = create_app()
    with app.app_context():
        init_db()
        logger.info("Starting inject system migration...")

        # Step 1: Create rubric_item table if it doesn't exist
        if not table_exists("rubric_item"):
            logger.info("Creating rubric_item table...")
            db.session.execute(db.text("""
                CREATE TABLE rubric_item (
                    id INTEGER NOT NULL AUTO_INCREMENT,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    points INTEGER NOT NULL,
                    `order` INTEGER DEFAULT 0,
                    template_id INTEGER,
                    PRIMARY KEY (id),
                    FOREIGN KEY (template_id) REFERENCES template(id)
                )
            """))
            db.session.commit()
            logger.info("rubric_item table created.")
        else:
            logger.info("rubric_item table already exists, skipping.")

        # Step 2: Create inject_rubric_score table if it doesn't exist
        if not table_exists("inject_rubric_score"):
            logger.info("Creating inject_rubric_score table...")
            db.session.execute(db.text("""
                CREATE TABLE inject_rubric_score (
                    id INTEGER NOT NULL AUTO_INCREMENT,
                    score INTEGER NOT NULL,
                    inject_id INTEGER,
                    rubric_item_id INTEGER,
                    grader_id INTEGER,
                    PRIMARY KEY (id),
                    FOREIGN KEY (inject_id) REFERENCES inject(id),
                    FOREIGN KEY (rubric_item_id) REFERENCES rubric_item(id),
                    FOREIGN KEY (grader_id) REFERENCES users(id)
                )
            """))
            db.session.commit()
            logger.info("inject_rubric_score table created.")
        else:
            logger.info("inject_rubric_score table already exists, skipping.")

        # Step 3: Create inject_comment table and migrate data from comment
        if not table_exists("inject_comment"):
            logger.info("Creating inject_comment table...")
            db.session.execute(db.text("""
                CREATE TABLE inject_comment (
                    id INTEGER NOT NULL AUTO_INCREMENT,
                    content TEXT NOT NULL,
                    created DATETIME,
                    is_read BOOLEAN DEFAULT FALSE,
                    inject_id INTEGER,
                    user_id INTEGER,
                    PRIMARY KEY (id),
                    FOREIGN KEY (inject_id) REFERENCES inject(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """))
            db.session.commit()

            if table_exists("comment"):
                logger.info("Migrating data from comment to inject_comment...")
                db.session.execute(db.text("""
                    INSERT INTO inject_comment (id, content, created, inject_id, user_id)
                    SELECT id, comment, time, inject_id, user_id FROM comment
                """))
                db.session.commit()
                logger.info("Comment data migrated.")
            logger.info("inject_comment table created.")
        else:
            logger.info("inject_comment table already exists, skipping.")

        # Step 4: Create inject_file table and migrate data from file
        if not table_exists("inject_file"):
            logger.info("Creating inject_file table...")
            db.session.execute(db.text("""
                CREATE TABLE inject_file (
                    id INTEGER NOT NULL AUTO_INCREMENT,
                    filename TEXT NOT NULL,
                    original_filename TEXT,
                    uploaded DATETIME,
                    inject_id INTEGER,
                    user_id INTEGER,
                    PRIMARY KEY (id),
                    FOREIGN KEY (inject_id) REFERENCES inject(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """))
            db.session.commit()

            if table_exists("file"):
                logger.info("Migrating data from file to inject_file...")
                db.session.execute(db.text("""
                    INSERT INTO inject_file (id, filename, inject_id, user_id)
                    SELECT id, name, inject_id, user_id FROM file
                """))
                db.session.commit()
                logger.info("File data migrated.")
            logger.info("inject_file table created.")
        else:
            logger.info("inject_file table already exists, skipping.")

        # Step 5: Create "Legacy Score" RubricItem for each template that has a score column
        if column_exists("template", "score"):
            # Check if we already migrated rubric items
            existing_count = db.session.execute(
                db.text("SELECT COUNT(*) FROM rubric_item")
            ).scalar()
            if existing_count == 0:
                logger.info("Creating Legacy Score rubric items from template.score...")
                templates = db.session.execute(
                    db.text("SELECT id, score FROM template")
                ).fetchall()
                for t in templates:
                    template_id, score = t[0], t[1]
                    if score is None:
                        score = 100
                    db.session.execute(
                        db.text(
                            "INSERT INTO rubric_item (title, description, points, `order`, template_id) "
                            "VALUES (:title, :desc, :points, 0, :tid)"
                        ),
                        {"title": "Legacy Score", "desc": "", "points": int(score), "tid": template_id},
                    )
                db.session.commit()
                logger.info("Legacy rubric items created.")
            else:
                logger.info("Rubric items already exist, skipping legacy score migration.")

        # Step 6: Create InjectRubricScore for each graded inject that has a score column
        if column_exists("inject", "score"):
            existing_scores = db.session.execute(
                db.text("SELECT COUNT(*) FROM inject_rubric_score")
            ).scalar()
            if existing_scores == 0:
                logger.info("Creating rubric scores from inject.score for graded injects...")
                graded_injects = db.session.execute(
                    db.text(
                        "SELECT i.id, i.score, i.template_id FROM inject i "
                        "WHERE i.status = 'Graded' AND i.score IS NOT NULL AND i.score > 0"
                    )
                ).fetchall()
                for inj in graded_injects:
                    inject_id, score, template_id = inj[0], inj[1], inj[2]
                    # Find the rubric item for this template
                    rubric_item = db.session.execute(
                        db.text(
                            "SELECT id FROM rubric_item WHERE template_id = :tid LIMIT 1"
                        ),
                        {"tid": template_id},
                    ).fetchone()
                    if rubric_item:
                        db.session.execute(
                            db.text(
                                "INSERT INTO inject_rubric_score (score, inject_id, rubric_item_id) "
                                "VALUES (:score, :iid, :rid)"
                            ),
                            {"score": int(score), "iid": inject_id, "rid": rubric_item[0]},
                        )
                db.session.commit()
                logger.info("Rubric scores created.")
            else:
                logger.info("Rubric scores already exist, skipping.")

        # Step 7: Drop old tables and columns (only if new tables exist)
        if table_exists("inject_comment") and table_exists("comment"):
            logger.info("Dropping old comment table...")
            db.session.execute(db.text("DROP TABLE comment"))
            db.session.commit()

        if table_exists("inject_file") and table_exists("file"):
            logger.info("Dropping old file table...")
            db.session.execute(db.text("DROP TABLE file"))
            db.session.commit()

        if column_exists("template", "score"):
            logger.info("Dropping template.score column...")
            db.session.execute(db.text("ALTER TABLE template DROP COLUMN score"))
            db.session.commit()

        if column_exists("inject", "score"):
            logger.info("Dropping inject.score column...")
            db.session.execute(db.text("ALTER TABLE inject DROP COLUMN score"))
            db.session.commit()

        logger.info("Migration complete!")


if __name__ == "__main__":
    migrate()
