from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DHLGHApplicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    planning_authority: str
    source_entity: str
    application_ref: str
    development_description: str
    site_address: Optional[str] = None
    site_postcode: Optional[str] = None
    site_geometry: Optional[str] = None  # WKT, parsed to geometry at the DB layer
    itm_easting: Optional[float] = None
    itm_northing: Optional[float] = None
    application_type: Optional[str] = None

    planning_status_current: str
    decision: Optional[str] = None
    date_received: date
    decision_due_date: Optional[date] = None
    decision_date: Optional[date] = None
    withdrawn_date: Optional[date] = None
    grant_date: Optional[date] = None
    expiry_date: Optional[date] = None

    appeal_ref_number: Optional[str] = None
    appeal_status: Optional[str] = None
    appeal_decision: Optional[str] = None
    appeal_decision_date: Optional[date] = None
    appeal_submitted_date: Optional[date] = None

    fi_request_date: Optional[date] = None
    fi_received_date: Optional[date] = None

    official_detail_url: Optional[str] = None
    site_id: Optional[str] = None

    source_system: str
    source_ingested_at: datetime = Field(default_factory=datetime.now)
    raw_payload_json: dict = Field(default_factory=dict)
