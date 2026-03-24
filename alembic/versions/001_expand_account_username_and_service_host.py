"""Expand account username and service host columns to 256 chars

Revision ID: 001
Revises: None
Create Date: 2026-03-24

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Account.username: String(50) -> String(256)
    op.alter_column(
        "accounts",
        "username",
        existing_type=sa.String(50),
        type_=sa.String(256),
        existing_nullable=False,
    )
    # Service.host: String(50) -> String(256)
    op.alter_column(
        "services",
        "host",
        existing_type=sa.String(50),
        type_=sa.String(256),
        existing_nullable=False,
    )


def downgrade():
    op.alter_column(
        "accounts",
        "username",
        existing_type=sa.String(256),
        type_=sa.String(50),
        existing_nullable=False,
    )
    op.alter_column(
        "services",
        "host",
        existing_type=sa.String(256),
        type_=sa.String(50),
        existing_nullable=False,
    )
