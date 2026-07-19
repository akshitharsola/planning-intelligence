"""create dhlgh_applications

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('dhlgh_applications',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('planning_authority', sa.String(), nullable=False),
    sa.Column('source_entity', sa.String(), nullable=False),
    sa.Column('application_ref', sa.String(), nullable=False),
    sa.Column('development_description', sa.String(), nullable=False),
    sa.Column('site_address', sa.String(), nullable=True),
    sa.Column('site_postcode', sa.String(), nullable=True),
    sa.Column('site_geometry', geoalchemy2.types.Geometry(srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('itm_easting', sa.Float(), nullable=True),
    sa.Column('itm_northing', sa.Float(), nullable=True),
    sa.Column('application_type', sa.String(), nullable=True),
    sa.Column('planning_status_current', sa.String(), nullable=False),
    sa.Column('decision', sa.String(), nullable=True),
    sa.Column('date_received', sa.Date(), nullable=False),
    sa.Column('decision_due_date', sa.Date(), nullable=True),
    sa.Column('decision_date', sa.Date(), nullable=True),
    sa.Column('withdrawn_date', sa.Date(), nullable=True),
    sa.Column('grant_date', sa.Date(), nullable=True),
    sa.Column('expiry_date', sa.Date(), nullable=True),
    sa.Column('appeal_ref_number', sa.String(), nullable=True),
    sa.Column('appeal_status', sa.String(), nullable=True),
    sa.Column('appeal_decision', sa.String(), nullable=True),
    sa.Column('appeal_decision_date', sa.Date(), nullable=True),
    sa.Column('appeal_submitted_date', sa.Date(), nullable=True),
    sa.Column('fi_request_date', sa.Date(), nullable=True),
    sa.Column('fi_received_date', sa.Date(), nullable=True),
    sa.Column('official_detail_url', sa.String(), nullable=True),
    sa.Column('site_id', sa.String(), nullable=True),
    sa.Column('source_system', sa.String(), nullable=False),
    sa.Column('source_ingested_at', sa.DateTime(), nullable=False),
    sa.Column('raw_payload_json', sa.JSON(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('planning_authority', 'application_ref', name='uq_dhlgh_application_natural_key')
    )
    # NOTE: a GIST spatial index on dhlgh_applications.site_geometry is
    # created automatically by GeoAlchemy2's after_create DDL event
    # (Geometry columns default to spatial_index=True) — see the same note
    # on migration 0001's applications table. Adding an explicit
    # op.create_index call for it would raise DuplicateTable.
    op.create_index(
        'ix_dhlgh_applications_planning_status_current',
        'dhlgh_applications',
        ['planning_status_current'],
    )
    op.create_index(
        'ix_dhlgh_applications_date_received',
        'dhlgh_applications',
        ['date_received'],
    )


def downgrade() -> None:
    op.drop_index('ix_dhlgh_applications_date_received', table_name='dhlgh_applications')
    op.drop_index('ix_dhlgh_applications_planning_status_current', table_name='dhlgh_applications')
    op.drop_table('dhlgh_applications')
