"""create decision_documents and decision_items tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "decision_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("planning_authority", sa.String(), nullable=False),
        sa.Column("application_ref", sa.String(), nullable=False),
        sa.Column(
            "dhlgh_application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("dhlgh_applications.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("council_doc_id", sa.String(), nullable=False),
        sa.Column("doc_type", sa.String(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=False),
        sa.Column("content_sha256", sa.String(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("extraction_method", sa.String(), nullable=False, server_default="pdftotext"),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("parser_version", sa.String(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("stated_count", sa.Integer(), nullable=True),
        sa.Column("target_count", sa.Integer(), nullable=True),
        sa.Column("parsed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("extracted_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('validated', 'count_mismatch', 'needs_ocr', 'no_schedule', 'unparsed', 'unverified', 'batch_order', 'rfi_order')",
            name="ck_decision_documents_status",
        ),
        sa.UniqueConstraint(
            "planning_authority",
            "council_doc_id",
            name="uq_decision_documents_authority_doc_id",
        ),
    )

    op.create_index(
        "ix_decision_documents_authority_ref",
        "decision_documents",
        ["planning_authority", "application_ref"],
    )

    op.create_table(
        "decision_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("decision_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("item_no", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("reason_text", sa.Text(), nullable=True),
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english', text || ' ' || coalesce(reason_text, ''))", persisted=True),
            nullable=True,
        ),
        sa.CheckConstraint(
            "kind IN ('condition', 'refusal_reason')",
            name="ck_decision_items_kind",
        ),
        sa.UniqueConstraint(
            "document_id",
            "item_no",
            name="uq_decision_items_doc_id_item_no",
        ),
    )

    op.create_index(
        "ix_decision_items_search_vector",
        "decision_items",
        ["search_vector"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_decision_items_search_vector", table_name="decision_items")
    op.drop_table("decision_items")
    op.drop_index("ix_decision_documents_authority_ref", table_name="decision_documents")
    op.drop_table("decision_documents")

