import uuid
from datetime import date, datetime

from geoalchemy2 import Geometry
from sqlalchemy import JSON, Date, DateTime, Float, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import Base


class DHLGHApplication(Base):
    __tablename__ = "dhlgh_applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    planning_authority: Mapped[str] = mapped_column(String, nullable=False)
    source_entity: Mapped[str] = mapped_column(String, nullable=False)
    application_ref: Mapped[str] = mapped_column(String, nullable=False)
    development_description: Mapped[str] = mapped_column(String, nullable=False)
    site_address: Mapped[str | None] = mapped_column(String, nullable=True)
    site_postcode: Mapped[str | None] = mapped_column(String, nullable=True)
    site_geometry = mapped_column(Geometry(geometry_type="GEOMETRY", srid=4326), nullable=True)
    itm_easting: Mapped[float | None] = mapped_column(Float, nullable=True)
    itm_northing: Mapped[float | None] = mapped_column(Float, nullable=True)
    application_type: Mapped[str | None] = mapped_column(String, nullable=True)

    planning_status_current: Mapped[str] = mapped_column(String, nullable=False)
    decision: Mapped[str | None] = mapped_column(String, nullable=True)
    date_received: Mapped[date] = mapped_column(Date, nullable=False)
    decision_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    decision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    withdrawn_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    grant_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    appeal_ref_number: Mapped[str | None] = mapped_column(String, nullable=True)
    appeal_status: Mapped[str | None] = mapped_column(String, nullable=True)
    appeal_decision: Mapped[str | None] = mapped_column(String, nullable=True)
    appeal_decision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    appeal_submitted_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    fi_request_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    fi_received_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    official_detail_url: Mapped[str | None] = mapped_column(String, nullable=True)
    site_id: Mapped[str | None] = mapped_column(String, nullable=True)

    source_system: Mapped[str] = mapped_column(String, nullable=False)
    source_ingested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    raw_payload_json: Mapped[dict] = mapped_column(JSON, default=dict)

    __table_args__ = (
        UniqueConstraint(
            "planning_authority", "application_ref", name="uq_dhlgh_application_natural_key"
        ),
    )
