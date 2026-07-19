"""
Resolve stage: dedup applications by the natural key
(planning_authority + application_ref) and generate an ApplicationEvent
for each ingested row, per spec section 4 / dev-plan section 6.5.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.models.application import Application
from src.core.models.application_event import ApplicationEvent
from src.core.models.dhlgh_application import DHLGHApplication
from src.core.schemas.application import ApplicationCreate
from src.core.schemas.dhlgh_application import DHLGHApplicationCreate


def resolve_and_upsert(session: Session, app_create: ApplicationCreate) -> Application:
    existing = session.scalar(
        select(Application).where(
            Application.planning_authority == app_create.planning_authority,
            Application.application_ref == app_create.application_ref,
        )
    )

    if existing is None:
        application = Application(**app_create.model_dump(exclude={"site_geometry"}))
        session.add(application)
        session.flush()
    else:
        for field, value in app_create.model_dump(exclude={"site_geometry"}).items():
            setattr(existing, field, value)
        application = existing
        session.flush()

    event = ApplicationEvent(
        application_id=application.id,
        application_ref=app_create.application_ref,
        planning_authority=app_create.planning_authority,
        event_type=app_create.status_event_type or "APPLICATION_RECEIVED",
        event_date=app_create.date_received,
        source_file=app_create.source_file,
        raw_payload_json=app_create.raw_payload_json,
    )
    session.add(event)
    return application


def resolve_and_upsert_dhlgh(
    session: Session, app_create: DHLGHApplicationCreate
) -> DHLGHApplication:
    """Dedup DHLGH rows by (planning_authority, application_ref) against
    dhlgh_applications — same natural-key pattern as resolve_and_upsert()
    above. No ApplicationEvent-equivalent emitted for this source (spec
    section 5): DHLGH's own ApplicationStatus/Decision/appeal fields
    already carry enough lifecycle state per row."""
    existing = session.scalar(
        select(DHLGHApplication).where(
            DHLGHApplication.planning_authority == app_create.planning_authority,
            DHLGHApplication.application_ref == app_create.application_ref,
        )
    )

    if existing is None:
        application = DHLGHApplication(**app_create.model_dump())
        session.add(application)
        session.flush()
    else:
        for field, value in app_create.model_dump().items():
            setattr(existing, field, value)
        application = existing
        session.flush()

    return application
