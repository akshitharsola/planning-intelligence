from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OtherRegulatoryFlags(BaseModel):
    ipc_licence: bool = False
    waste_licence: bool = False


class ApplicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Core
    planning_authority: str
    source_entity: str
    application_ref: str
    application_ref_type: Optional[str] = None
    applicant_name: str
    site_address: Optional[str] = None
    site_locality: Optional[str] = None
    site_county: Optional[str] = None
    site_geometry: Optional[str] = None  # WKT, parsed to geometry at the DB layer
    development_description: str
    application_type: str

    # Lifecycle and status
    planning_status_current: str
    status_event_type: Optional[str] = None
    date_received: date
    decision_due_date: Optional[date] = None
    decision_date: Optional[date] = None
    further_information_flag: bool = False
    protected_structure_flag: bool = False
    eia_eis_flag: bool = False
    other_regulatory_flags: OtherRegulatoryFlags = Field(default_factory=OtherRegulatoryFlags)

    # Provenance
    official_detail_url: Optional[str] = None
    official_documents_url: Optional[str] = None
    source_system: str
    source_file: str
    source_ingested_at: datetime = Field(default_factory=datetime.now)
    raw_payload_json: dict = Field(default_factory=dict)

    # Market layer
    market_entity: Optional[str] = None
    commuter_belt_flag: bool = False
