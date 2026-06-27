from datetime import date

from pydantic import BaseModel, ConfigDict, Field

EVENT_TYPES = {
    "APPLICATION_RECEIVED",
    "FURTHER_INFORMATION_REQUESTED",
    "FURTHER_INFORMATION_RECEIVED",
    "DECISION_GRANTED",
    "DECISION_REFUSED",
    "APPLICATION_WITHDRAWN",
    "APPLICATION_INVALID",
    "APPEAL_LODGED",
    "APPEAL_DECIDED",
}


class ApplicationEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application_ref: str
    planning_authority: str
    event_type: str
    event_date: date
    source_file: str
    raw_payload_json: dict = Field(default_factory=dict)
