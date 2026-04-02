"""Add category column to template table

Revision ID: 002
Revises: 001
Create Date: 2026-04-01

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("template") as batch_op:
        batch_op.add_column(sa.Column("category", sa.String(50), nullable=True))


def downgrade():
    with op.batch_alter_table("template") as batch_op:
        batch_op.drop_column("category")
