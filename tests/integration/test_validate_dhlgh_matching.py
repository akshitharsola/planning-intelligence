import uuid

import sqlalchemy as sa

from scripts.validate_dhlgh_matching import build_validation_report
from src.core.db.session import SessionLocal
from src.core.models.application import Application
from src.core.models.dhlgh_application import DHLGHApplication


def _cleanup(session):
    session.execute(sa.text("DELETE FROM applications WHERE application_ref LIKE 'VALTEST/%'"))
    session.execute(sa.text("DELETE FROM dhlgh_applications WHERE application_ref LIKE 'VALTEST/%'"))
    session.commit()


def test_build_validation_report_counts_rung1_match_and_no_match():
    session = SessionLocal()
    try:
        _cleanup(session)

        session.add(Application(
            id=uuid.uuid4(),
            planning_authority="Galway County Council",
            source_entity="GALWAY_COUNTY",
            application_ref="VALTEST/001",
            applicant_name="Test",
            site_address="Test address one",
            development_description="Test",
            application_type="Permission",
            planning_status_current="Received",
            date_received="2026-01-01",
            source_system="test",
            source_file="test",
        ))
        session.add(DHLGHApplication(
            id=uuid.uuid4(),
            planning_authority="Galway County Council",
            source_entity="DHLGH_NATIONAL",
            application_ref="VALTEST/001",
            development_description="Test",
            site_address="Test address one",
            planning_status_current="Received",
            date_received="2026-01-01",
            source_system="test",
        ))
        session.add(DHLGHApplication(
            id=uuid.uuid4(),
            planning_authority="Galway County Council",
            source_entity="DHLGH_NATIONAL",
            application_ref="VALTEST/999",
            development_description="Test",
            site_address="Totally unrelated address",
            planning_status_current="Received",
            date_received="2026-01-01",
            source_system="test",
        ))
        session.commit()

        report = build_validation_report(session, authority_filter="Galway County Council", ref_prefix="VALTEST/")

        assert report["by_rung"]["rung_1"] == 1
        assert report["by_rung"]["no_match"] == 1
        assert report["total_dhlgh_rows"] == 2
    finally:
        _cleanup(session)
        session.close()
