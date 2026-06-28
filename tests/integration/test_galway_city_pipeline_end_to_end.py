from src.core.db.session import SessionLocal
from src.pipelines.normalize import normalize_row
from src.pipelines.publish import publish
from src.pipelines.resolve import resolve_and_upsert

REGION_CONFIG = {
    "source_entity": "GALWAY_CITY_COUNCIL",
    "planning_authority": "Galway City Council",
}


def test_normalize_resolve_publish_roundtrip():
    raw_row = {
        "file_number": "TEST/0001",
        "applicant": "Test Applicant",
        "app_type": "P",
        "date_received": "02/03/2026",
        "description": "Test development at Bohermore Galway",
    }
    app_create = normalize_row(raw_row, source_type="received", region_config=REGION_CONFIG,
                               source_file="test.pdf")

    session = SessionLocal()
    try:
        application = resolve_and_upsert(session, app_create)
        publish(session, region="galway_city", rows_ingested=1, parse_errors=0)
        assert application.application_ref == "TEST/0001"
    finally:
        session.close()
