"""
Maps a raw parser row (dict, source-specific keys) into the canonical
ApplicationCreate schema. source_type comes from the pdf_patterns key
the file matched (see config/galway/city.yaml).
"""

from datetime import datetime

from src.core.normalization.location import extract_location
from src.core.schemas.application import ApplicationCreate, OtherRegulatoryFlags

_SOURCE_TYPE_TO_STATUS = {
    "received": ("Received", "APPLICATION_RECEIVED"),
    "granted": ("Granted", "DECISION_GRANTED"),
    "refused": ("Refused", "DECISION_REFUSED"),
    "invalid": ("Invalid", "APPLICATION_INVALID"),
    "firvalidated": ("Received", "APPLICATION_RECEIVED"),
    "further_recd": ("Further Info", "FURTHER_INFORMATION_RECEIVED"),
    "further_reqd": ("Further Info", "FURTHER_INFORMATION_REQUESTED"),
}


def normalize_row(raw_row: dict, source_type: str, region_config: dict,
                   source_file: str) -> ApplicationCreate:
    status, event_type = _SOURCE_TYPE_TO_STATUS.get(source_type, ("Received", "APPLICATION_RECEIVED"))
    description = raw_row.get("description", "")
    location = extract_location(description)

    date_received = _parse_date(raw_row.get("date_received")) or datetime.now().date()
    decision_date = _parse_date(raw_row.get("mo_date"))

    return ApplicationCreate(
        planning_authority=region_config["planning_authority"],
        source_entity=region_config["source_entity"],
        application_ref=raw_row.get("file_number", ""),
        applicant_name=raw_row.get("applicant", ""),
        site_address=location["address"],
        site_locality=location["area"],
        site_county="Galway",
        development_description=description,
        application_type=_expand_app_type(raw_row.get("app_type", "")),
        planning_status_current=status,
        status_event_type=event_type,
        date_received=date_received,
        decision_date=decision_date,
        further_information_flag=source_type in ("further_recd", "further_reqd"),
        protected_structure_flag=_flag_yes(raw_row.get("protected_structure", "")),
        eia_eis_flag=_flag_yes(raw_row.get("eis", "")),
        other_regulatory_flags=OtherRegulatoryFlags(
            ipc_licence=_flag_yes(raw_row.get("ipc_licence", "")),
            waste_licence=_flag_yes(raw_row.get("waste_licence", "")),
        ),
        source_system="Galway City Weekly Lists PDF",
        source_file=source_file,
        raw_payload_json=raw_row,
    )


def _flag_yes(val: str) -> bool:
    return str(val).strip().upper() in ("Y", "YES", "TRUE", "1")


def _expand_app_type(code: str) -> str:
    return {"P": "Permission", "R": "Retention", "O": "Outline"}.get(code.strip().upper(), code or "Permission")


def _parse_date(value):
    if not value:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None
