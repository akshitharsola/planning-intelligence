import uuid
from datetime import date, datetime

from geoalchemy2 import Geometry
from sqlalchemy import JSON, Boolean, Date, DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import Base


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Core
    planning_authority: Mapped[str] = mapped_column(String, nullable=False)
    source_entity: Mapped[str] = mapped_column(String, nullable=False)
    application_ref: Mapped[str] = mapped_column(String, nullable=False)
    application_ref_type: Mapped[str | None] = mapped_column(String, nullable=True)
    applicant_name: Mapped[str] = mapped_column(String, nullable=False)
    site_address: Mapped[str | None] = mapped_column(String, nullable=True)
    site_locality: Mapped[str | None] = mapped_column(String, nullable=True)
    site_county: Mapped[str | None] = mapped_column(String, nullable=True)
    site_geometry = mapped_column(Geometry(geometry_type="GEOMETRY", srid=4326), nullable=True)
    development_description: Mapped[str] = mapped_column(String, nullable=False)
    application_type: Mapped[str] = mapped_column(String, nullable=False)

    # Lifecycle and status
    planning_status_current: Mapped[str] = mapped_column(String, nullable=False)
    status_event_type: Mapped[str | None] = mapped_column(String, nullable=True)
    date_received: Mapped[date] = mapped_column(Date, nullable=False)
    decision_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    decision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    further_information_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    protected_structure_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    eia_eis_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    other_regulatory_flags: Mapped[dict] = mapped_column(JSON, default=dict)

    # Provenance
    official_detail_url: Mapped[str | None] = mapped_column(String, nullable=True)
    official_documents_url: Mapped[str | None] = mapped_column(String, nullable=True)
    source_system: Mapped[str] = mapped_column(String, nullable=False)
    source_file: Mapped[str] = mapped_column(String, nullable=False)
    source_ingested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    raw_payload_json: Mapped[dict] = mapped_column(JSON, default=dict)

    # Market layer
    market_entity: Mapped[str | None] = mapped_column(String, nullable=True)
    commuter_belt_flag: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("planning_authority", "application_ref", name="uq_application_natural_key"),
    )
