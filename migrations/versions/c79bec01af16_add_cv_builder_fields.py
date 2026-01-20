"""Add cv builder fields

Revision ID: c79bec01af16
Revises: 34ac89ef295d
Create Date: 2026-01-20 10:57:59.414744

"""

from alembic import op
import sqlalchemy as sa


revision = "c79bec01af16"
down_revision = "34ac89ef295d"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("cv_files", schema=None) as batch_op:
        batch_op.add_column(sa.Column("cv_source", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("structured_data", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("section_scores", sa.JSON(), nullable=True))
        batch_op.alter_column(
            "file_url", existing_type=sa.VARCHAR(length=500), nullable=True
        )


def downgrade():
    with op.batch_alter_table("cv_files", schema=None) as batch_op:
        batch_op.alter_column(
            "file_url", existing_type=sa.VARCHAR(length=500), nullable=False
        )
        batch_op.drop_column("section_scores")
        batch_op.drop_column("structured_data")
        batch_op.drop_column("cv_source")
