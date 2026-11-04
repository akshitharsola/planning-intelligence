import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Computed, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db.base import Base

if TYPE_CHECKING:
    from src.core.models.decision_document import DecisionDocument


ALLOWED_ITEM_KINDS = (
    "condition",
    "refusal_reason",
)


class DecisionItem(Base):
    __tablename__ = "decision_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("decision_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_no: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    reason_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    search_vector = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', text || ' ' || coalesce(reason_text, ''))", persisted=True),
        nullable=True,
    )

    document: Mapped["DecisionDocument"] = relationship(
        "DecisionDocument", back_populates="items"
    )

    __table_args__ = (
        CheckConstraint(
            f"kind IN {ALLOWED_ITEM_KINDS}",
            name="ck_decision_items_kind",
        ),
        UniqueConstraint(
            "document_id",
            "item_no",
            name="uq_decision_items_doc_id_item_no",
        ),
        Index(
            "ix_decision_items_search_vector",
            "search_vector",
            postgresql_using="gin",
        ),
    )

