"""
County normalization maps Galway County Council's ArcGIS Feature Service
attributes directly to the canonical ApplicationCreate schema. Unlike City,
there is no source_type-per-PDF-list convention here — status is derived
from the record's own Decision/ApplicationStatus fields (verified against
live data: e.g. ApplicationStatus="Application Finalised" with
Decision="Granted (Conditional)" or "Refused"; ApplicationStatus alone
covers Withdrawn/Incompleted App/Deemed Withdrawal cases where Decision is
the "n\\a" null sentinel).

site_locality extraction reuses City's status/date helpers (both
authority-agnostic) but skips City's neighbourhood gazetteer in
src/core/normalization/location.py, since County's Location field is a
townland/place name, not a City-style street address — left as a plain
pass-through of Location for this pass.
"""

from datetime import date, datetime

from src.pipelines.normalize import _parse_date
from src.core.schemas.application import ApplicationCreate, OtherRegulatoryFlags

_NULL_SENTINELS = {"n/a", "n\\a", "na", "none", "null", "", "-"}


def normalize_county_row(raw_row: dict, region_config: dict, source_file: str) -> ApplicationCreate:
    application_ref = _clean_str(raw_row.get("ApplicationNumber"))
    if not application_ref:
        raise ValueError(
            f"County record missing ApplicationNumber (OBJECTID={raw_row.get('OBJECTID')!r}); "
            "refusing to normalize a row with a blank natural-key component."
        )

    status, event_type = _derive_status(
        raw_row.get("ApplicationStatus"), raw_row.get("Decision"), raw_row.get("AppealDecision")
    )
    description = _clean_str(raw_row.get("Description")) or ""
    date_received = _parse_date(_arcgis_date(raw_row.get("ReceivedDate"))) or date.today()
    decision_date = _parse_date(_arcgis_date(raw_row.get("DecisionDate")))
    decision_due_date = _parse_date(_arcgis_date(raw_row.get("DecisionDueDate")))

    return ApplicationCreate(
        planning_authority=region_config["planning_authority"],
        source_entity=region_config["source_entity"],
        application_ref=application_ref,
        applicant_name=_clean_str(raw_row.get("ApplicantName")) or "",
        site_address=_clean_str(raw_row.get("Location")),
        site_locality=None,
        site_county="Galway",
        development_description=description,
        application_type=_clean_str(raw_row.get("ApplicationType")) or "Permission",
        planning_status_current=status,
        status_event_type=event_type,
        date_received=date_received,
        decision_due_date=decision_due_date,
        decision_date=decision_date,
        protected_structure_flag=False,
        eia_eis_flag=False,
        other_regulatory_flags=OtherRegulatoryFlags(),
        official_documents_url=_clean_str(raw_row.get("MoreInfo")),
        source_system="Galway County Council ArcGIS Feature Service",
        source_file=source_file,
        raw_payload_json=raw_row,
    )


def _clean_str(value) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return None if cleaned.lower() in _NULL_SENTINELS else cleaned or None


def _arcgis_date(value) -> str | None:
    """ArcGIS dates here are DD/MM/YYYY strings; reject null-sentinel values."""
    cleaned = _clean_str(value)
    return cleaned


def _derive_status(application_status, decision, appeal_decision=None) -> tuple[str, str]:
    decision_clean = _clean_str(decision)
    status_clean = _clean_str(application_status)
    appeal_clean = _clean_str(appeal_decision)

    if decision_clean:
        decision_lower = decision_clean.lower()
        if "grant" in decision_lower:
            return "Granted", "DECISION_GRANTED"
        if "refus" in decision_lower:
            return "Refused", "DECISION_REFUSED"

    if appeal_clean:
        appeal_lower = appeal_clean.lower()
        if "grant" in appeal_lower:
            return "Granted", "DECISION_GRANTED"
        if "refus" in appeal_lower:
            return "Refused", "DECISION_REFUSED"

    if decision_clean:
        return "Unknown/Needs Review", "STATUS_UNRECOGNIZED"

    if status_clean:
        status_lower = status_clean.lower()
        if "withdraw" in status_lower:
            return "Withdrawn", "APPLICATION_WITHDRAWN"
        if "incomplete" in status_lower:
            return "Invalid", "APPLICATION_INVALID"

    return "Received", "APPLICATION_RECEIVED"
