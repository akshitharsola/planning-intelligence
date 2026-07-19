import sqlalchemy as sa

from src.core.db.session import SessionLocal
from src.core.normalization.dhlgh import normalize_dhlgh_row
from src.pipelines.publish import publish
from src.pipelines.resolve import resolve_and_upsert_dhlgh

REGION_CONFIG = {
    "source_entity": "DHLGH_NATIONAL",
}


def _cleanup():
    session = SessionLocal()
    try:
        session.execute(
            sa.text("DELETE FROM dhlgh_applications WHERE application_ref LIKE 'ROUNDTRIP/%'")
        )
        session.commit()
    finally:
        session.close()


def test_normalize_resolve_publish_roundtrip():
    _cleanup()
    try:
        raw_row = {
            "OBJECTID": 900001,
            "PlanningAuthority": "Galway City Council",
            "ApplicationNumber": "ROUNDTRIP/0001",
            "DevelopmentDescription": "Test development at Bohermore Galway",
            "DevelopmentAddress": "Bohermore, Galway",
            "ApplicationStatus": "Received",
            "ReceivedDate": "02/03/2026",
        }
        app_create = normalize_dhlgh_row(
            raw_row, region_config=REGION_CONFIG, source_file="dhlgh:900001"
        )

        session = SessionLocal()
        try:
            application = resolve_and_upsert_dhlgh(session, app_create)
            publish(session, region="dhlgh_galway", rows_ingested=1, parse_errors=0)
            assert application.application_ref == "ROUNDTRIP/0001"
            assert application.planning_authority == "Galway City Council"
        finally:
            session.close()
    finally:
        _cleanup()


def test_resolve_and_upsert_dhlgh_updates_existing_row_on_status_change():
    _cleanup()
    try:
        session = SessionLocal()
        try:
            raw_row = {
                "OBJECTID": 900002,
                "PlanningAuthority": "Galway County Council",
                "ApplicationNumber": "ROUNDTRIP/0002",
                "DevelopmentDescription": "Test",
                "ApplicationStatus": "Received",
                "ReceivedDate": "01/01/2026",
            }
            first = normalize_dhlgh_row(
                raw_row, region_config=REGION_CONFIG, source_file="dhlgh:900002"
            )
            application = resolve_and_upsert_dhlgh(session, first)
            first_id = application.id
            session.commit()

            raw_row_updated = dict(raw_row, ApplicationStatus="Granted", Decision="Granted")
            second = normalize_dhlgh_row(
                raw_row_updated, region_config=REGION_CONFIG, source_file="dhlgh:900002"
            )
            updated = resolve_and_upsert_dhlgh(session, second)
            session.commit()

            assert updated.id == first_id
            assert updated.planning_status_current == "Granted"

            count = session.execute(
                sa.text(
                    "SELECT COUNT(*) FROM dhlgh_applications WHERE application_ref = 'ROUNDTRIP/0002'"
                )
            ).scalar()
            assert count == 1
        finally:
            session.close()
    finally:
        _cleanup()
