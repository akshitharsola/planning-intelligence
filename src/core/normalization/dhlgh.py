"""
DHLGH normalization maps the national ArcGIS Feature Service's `attributes`
dict (plus an optional `_geometry` key stitched in by DHLGHScraper, spec
section 3) into the DHLGHApplicationCreate schema (spec section 6).

Distinct from County/City normalization: this source carries its own
appeal-lifecycle fields and ITM coordinates as first-class columns, and a
polygon site geometry (`rings`, in the ArcGIS JSON response's Esri
polygon shape) that neither existing Galway source has. No shapely
dependency is added for this — the rings-to-WKT conversion here is a
small, self-contained polygon serializer, since DHLGH's ArcGIS response is
guaranteed one specific shape (Esri JSON polygon rings) rather than
requiring general-purpose geometry parsing.
"""

from datetime import date

from src.pipelines.normalize import _parse_date
from src.core.schemas.dhlgh_application import DHLGHApplicationCreate

_NULL_SENTINELS = {"n/a", "n\\a", "na", "none", "null", "", "-"}


def normalize_dhlgh_row(raw_row: dict, region_config: dict, source_file: str) -> DHLGHApplicationCreate:
    application_ref = _clean_str(raw_row.get("ApplicationNumber"))
    if not application_ref:
        raise ValueError(
            f"DHLGH record missing ApplicationNumber (OBJECTID={raw_row.get('OBJECTID')!r}); "
            "refusing to normalize a row with a blank natural-key component."
        )

    planning_authority = _clean_str(raw_row.get("PlanningAuthority")) or region_config.get(
        "planning_authority", ""
    )
    description = _clean_str(raw_row.get("DevelopmentDescription")) or ""
    date_received = _parse_date(_arcgis_date(raw_row.get("ReceivedDate"))) or date.today()

    return DHLGHApplicationCreate(
        planning_authority=planning_authority,
        source_entity=region_config["source_entity"],
        application_ref=application_ref,
        development_description=description,
        site_address=_clean_str(raw_row.get("DevelopmentAddress")),
        site_postcode=_clean_str(raw_row.get("DevelopmentPostcode")),
        site_geometry=_rings_to_wkt(raw_row.get("_geometry")),
        itm_easting=_clean_float(raw_row.get("ITMEasting")),
        itm_northing=_clean_float(raw_row.get("ITMNorthing")),
        application_type=_clean_str(raw_row.get("ApplicationType")),
        planning_status_current=_clean_str(raw_row.get("ApplicationStatus")) or "Received",
        decision=_clean_str(raw_row.get("Decision")),
        date_received=date_received,
        decision_due_date=_parse_date(_arcgis_date(raw_row.get("DecisionDueDate"))),
        decision_date=_parse_date(_arcgis_date(raw_row.get("DecisionDate"))),
        withdrawn_date=_parse_date(_arcgis_date(raw_row.get("WithdrawnDate"))),
        grant_date=_parse_date(_arcgis_date(raw_row.get("GrantDate"))),
        expiry_date=_parse_date(_arcgis_date(raw_row.get("ExpiryDate"))),
        appeal_ref_number=_clean_str(raw_row.get("AppealRefNumber")),
        appeal_status=_clean_str(raw_row.get("AppealStatus")),
        appeal_decision=_clean_str(raw_row.get("AppealDecision")),
        appeal_decision_date=_parse_date(_arcgis_date(raw_row.get("AppealDecisionDate"))),
        appeal_submitted_date=_parse_date(_arcgis_date(raw_row.get("AppealSubmittedDate"))),
        fi_request_date=_parse_date(_arcgis_date(raw_row.get("FIRequestDate"))),
        fi_received_date=_parse_date(_arcgis_date(raw_row.get("FIRecDate"))),
        official_detail_url=_clean_str(raw_row.get("LinkAppDetails")),
        site_id=_clean_str(raw_row.get("SiteId")),
        source_system="DHLGH National Planning Dataset ArcGIS Feature Service",
        raw_payload_json=raw_row,
    )


def _clean_str(value) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return None if cleaned.lower() in _NULL_SENTINELS else cleaned or None


def _clean_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _arcgis_date(value) -> str | None:
    """DHLGH ArcGIS dates arrive as epoch milliseconds (unlike County's
    DD/MM/YYYY strings) when returned via the JSON REST API with numeric
    date storage — but the field may also come through as an
    already-formatted string depending on the layer's date field config,
    so both are handled here."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return date.fromtimestamp(value / 1000).isoformat()
    cleaned = _clean_str(value)
    return cleaned


def _rings_to_wkt(geometry: dict | None) -> str | None:
    """Converts an Esri JSON polygon (`{"rings": [[[x, y], ...], ...]}`)
    into EWKT POLYGON/MULTIPOLYGON text (SRID=4326 prefix), matching what
    the dhlgh_applications.site_geometry column's ST_GeomFromEWKT
    conversion function expects (geoalchemy2.Geometry(srid=4326)). Note
    the ArcGIS source's polygons are in ITM (EPSG:2157), not WGS84 — this
    tags the WKT 4326 only because that's the column's declared SRID; no
    reprojection is performed here. Returns None if no geometry or no
    rings are present — DHLGH does not guarantee geometry on every row."""
    if not geometry:
        return None
    rings = geometry.get("rings")
    if not rings:
        return None

    ring_wkts = []
    for ring in rings:
        if len(ring) < 3:
            continue
        points = ", ".join(f"{x} {y}" for x, y in ring)
        ring_wkts.append(f"({points})")

    if not ring_wkts:
        return None
    if len(ring_wkts) == 1:
        body = f"POLYGON ({ring_wkts[0]})"
    else:
        body = f"MULTIPOLYGON ({', '.join(f'({w})' for w in ring_wkts)})"
    return f"SRID=4326;{body}"
