"""create ingestion_state and ingested_files

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ingestion_state',
        sa.Column('region', sa.Text(), nullable=False),
        sa.Column('watermark', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('region'),
    )
    op.create_table(
        'ingested_files',
        sa.Column('region', sa.Text(), nullable=False),
        sa.Column('file_id', sa.Text(), nullable=False),
        sa.Column('ingested_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('region', 'file_id'),
    )


def downgrade() -> None:
    op.drop_table('ingested_files')
    op.drop_table('ingestion_state')
