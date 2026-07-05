"""add search indexes

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')

    op.create_index(
        'ix_applications_planning_status_current',
        'applications',
        ['planning_status_current'],
    )
    op.create_index(
        'ix_applications_application_type',
        'applications',
        ['application_type'],
    )
    op.create_index(
        'ix_applications_date_received',
        'applications',
        ['date_received'],
    )
    op.create_index(
        'ix_applications_applicant_name_trgm',
        'applications',
        ['applicant_name'],
        postgresql_using='gin',
        postgresql_ops={'applicant_name': 'gin_trgm_ops'},
    )
    op.create_index(
        'ix_applications_site_address_trgm',
        'applications',
        ['site_address'],
        postgresql_using='gin',
        postgresql_ops={'site_address': 'gin_trgm_ops'},
    )
    op.create_index(
        'ix_applications_development_description_trgm',
        'applications',
        ['development_description'],
        postgresql_using='gin',
        postgresql_ops={'development_description': 'gin_trgm_ops'},
    )


def downgrade() -> None:
    op.drop_index('ix_applications_development_description_trgm', table_name='applications')
    op.drop_index('ix_applications_site_address_trgm', table_name='applications')
    op.drop_index('ix_applications_applicant_name_trgm', table_name='applications')
    op.drop_index('ix_applications_date_received', table_name='applications')
    op.drop_index('ix_applications_application_type', table_name='applications')
    op.drop_index('ix_applications_planning_status_current', table_name='applications')
