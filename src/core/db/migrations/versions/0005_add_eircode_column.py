"""Add eircode column to applications

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-24

"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("eircode", sa.String(), nullable=True))
    op.create_index(
        "ix_applications_eircode",
        "applications",
        ["eircode"],
    )


def downgrade() -> None:
    op.drop_index("ix_applications_eircode", table_name="applications")
    op.drop_column("applications", "eircode")
