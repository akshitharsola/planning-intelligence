import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db.base import Base

if TYPE_CHECKING:
    from src.core.models.decision_item import DecisionItem
    from src.core.models.dhlgh_application import DHLGHApplication


ALLOWED_DOCUMENT_STATUSES = (
    "validated",
    "count_mismatch",
    "needs_ocr",
    "no_schedule",
    "unparsed",
    "unverified",
    "batch_order",
    "rfi_order",
)


class DecisionDocument(Base):
    __tablename__ = "decision_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    planning_authority: Mapped[str] = mapped_column(String, nullable=False)
    application_ref: Mapped[str] = mapped_column(String, nullable=False)
    dhlgh_application_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dhlgh_applications.id", ondelete="SET NULL"),
        nullable=True,
    )
    council_doc_id: Mapped[str] = mapped_column(String, nullable=False)
    doc_type: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str] = mapped_column(String, nullable=False)
    content_sha256: Mapped[str] = mapped_column(String, nullable=False)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extraction_method: Mapped[str] = mapped_column(String, nullable=False, default="pdftotext")
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    parser_version: Mapped[str] = mapped_column(String, nullable=False, default="1")
    status: Mapped[str] = mapped_column(String, nullable=False)
    stated_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parsed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    extracted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    items: Mapped[list["DecisionItem"]] = relationship(
        "DecisionItem",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    dhlgh_application: Mapped[Optional["DHLGHApplication"]] = relationship("DHLGHApplication")

    __table_args__ = (
        CheckConstraint(
            f"status IN {ALLOWED_DOCUMENT_STATUSES}",
            name="ck_decision_documents_status",
        ),
        UniqueConstraint(
            "planning_authority",
            "council_doc_id",
            name="uq_decision_documents_authority_doc_id",
        ),
        Index(
            "ix_decision_documents_authority_ref",
            "planning_authority",
            "application_ref",
        ),
    )
