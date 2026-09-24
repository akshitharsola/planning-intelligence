from sqlalchemy import text

from src.core.db.session import SessionLocal
from src.core.models.application_event import ApplicationEvent
from src.core.schemas.application import ApplicationCreate
from src.pipelines.resolve import resolve_and_upsert

REGION = "test_region_resolve_dedup"


def _make_app_create(**overrides) -> ApplicationCreate:
    defaults = dict(
        planning_authority=REGION,
        source_entity="TEST_ENTITY",
        application_ref="RESOLVE-DEDUP-1",
        applicant_name="Test Applicant",
        development_description="Test description",
        application_type="PERMISSION",
        planning_status_current="Received",
        date_received="2026-01-01",
        source_system="test_source_system",
        source_file="test_file.pdf",
    )
    defaults.update(overrides)
    return ApplicationCreate(**defaults)


def _cleanup(session):
    session.execute(
        text(
            "DELETE FROM application_events WHERE planning_authority = :region"
        ),
        {"region": REGION},
    )
    session.execute(
        text("DELETE FROM applications WHERE planning_authority = :region"),
        {"region": REGION},
    )
    session.commit()


def test_resolve_and_upsert_does_not_duplicate_identical_event():
    session = SessionLocal()
    try:
        _cleanup(session)

        app_create = _make_app_create()
        application = resolve_and_upsert(session, app_create)
        session.commit()

        # Re-ingest the exact same row again, as a re-run of ingestion would.
        resolve_and_upsert(session, _make_app_create())
        session.commit()

        events = (
            session.query(ApplicationEvent)
            .filter(ApplicationEvent.application_id == application.id)
            .all()
        )
        assert len(events) == 1
    finally:
        _cleanup(session)
        session.close()


def test_resolve_and_upsert_adds_new_event_when_status_changes():
    session = SessionLocal()
    try:
        _cleanup(session)

        application = resolve_and_upsert(session, _make_app_create())
        session.commit()

        resolve_and_upsert(
            session,
            _make_app_create(
                planning_status_current="Granted",
                status_event_type="DECISION_GRANTED",
                decision_date="2026-02-01",
            ),
        )
        session.commit()

        events = (
            session.query(ApplicationEvent)
            .filter(ApplicationEvent.application_id == application.id)
            .all()
        )
        assert len(events) == 2
    finally:
        _cleanup(session)
        session.close()
