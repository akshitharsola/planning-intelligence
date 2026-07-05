"""
Maps a raw parser row (dict, source-specific keys) into the canonical
ApplicationCreate schema. source_type comes from the pdf_patterns key
the file matched (see config/galway/city.yaml).
"""

import re
from datetime import datetime

from src.core.normalization.location import extract_location
from src.core.schemas.application import ApplicationCreate, OtherRegulatoryFlags

# Real Galway file numbers are "YY/NNNNN" (e.g. 26/60159); test fixtures use
# a readable "PREFIX/NNNN" convention. Both are a short alnum token, a
# slash, then digits only — this rejects the free-text/date-range values
# seen from non-application PDFs (licence lists) force-parsed into this
# schema, e.g. "01/01/2026 - 01/01/2027", "3 years requested",
# "Not Confirmed Yet". See config/galway/city.yaml pdf_patterns history for
# the incident this guards against.
_FILE_NUMBER_RE = re.compile(r"^[A-Za-z0-9]+/\d+$")

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
    file_number = str(raw_row.get("file_number", "")).strip()
    if not file_number:
        raise ValueError(
            f"City record missing file_number (source_file={source_file!r}); "
            "refusing to normalize a row with a blank natural-key component."
        )

    status, event_type = _SOURCE_TYPE_TO_STATUS.get(source_type, ("Received", "APPLICATION_RECEIVED"))
    description = raw_row.get("description", "")
    location = extract_location(description)

    date_received = _parse_date(raw_row.get("date_received")) or datetime.now().date()
    decision_date = _parse_date(raw_row.get("mo_date"))

    return ApplicationCreate(
        planning_authority=region_config["planning_authority"],
        source_entity=region_config["source_entity"],
        application_ref=file_number,
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


def is_plausible_application_row(app_create: ApplicationCreate) -> bool:
    """Reject rows that don't look like real planning applications.

    Guards against non-application PDFs (licence/declaration lists) being
    force-parsed into the applications schema by an over-broad pdf_patterns
    match. Callers should skip (not raise on) rows failing this check, and
    log them distinctly from parse/normalize failures.
    """
    if not _FILE_NUMBER_RE.match(app_create.application_ref or ""):
        return False
    if not app_create.applicant_name.strip():
        return False
    return True


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
