"""
County normalization reuses City's status/event mapping and date parsing
(both authority-agnostic) but skips Galway City's neighbourhood gazetteer
in src/core/normalization/location.py, since County addresses reference
towns (Oranmore, Tuam, ...) rather than City neighbourhoods. site_locality
extraction for County is left as a plain pass-through of the description
for this foundation pass — refining it is in scope for a future
parser-dev iteration once real address patterns are reviewed.
"""

from datetime import datetime

from src.pipelines.normalize import _SOURCE_TYPE_TO_STATUS, _expand_app_type, _flag_yes, _parse_date
from src.core.schemas.application import ApplicationCreate, OtherRegulatoryFlags


def normalize_county_row(raw_row: dict, source_type: str, region_config: dict,
                         source_file: str) -> ApplicationCreate:
    status, event_type = _SOURCE_TYPE_TO_STATUS.get(source_type, ("Received", "APPLICATION_RECEIVED"))
    description = raw_row.get("description", "")
    date_received = _parse_date(raw_row.get("date_received")) or datetime.now().date()

    return ApplicationCreate(
        planning_authority=region_config["planning_authority"],
        source_entity=region_config["source_entity"],
        application_ref=raw_row.get("file_number", ""),
        applicant_name=raw_row.get("applicant", ""),
        site_address=description,
        site_locality=None,
        site_county="Galway",
        development_description=description,
        application_type=_expand_app_type(raw_row.get("app_type", "")),
        planning_status_current=status,
        status_event_type=event_type,
        date_received=date_received,
        protected_structure_flag=_flag_yes(raw_row.get("protected_structure", "")),
        eia_eis_flag=_flag_yes(raw_row.get("eis", "")),
        other_regulatory_flags=OtherRegulatoryFlags(),
        source_system="Galway County Weekly Lists PDF",
        source_file=source_file,
        raw_payload_json=raw_row,
    )
