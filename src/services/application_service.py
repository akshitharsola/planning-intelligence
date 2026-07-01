from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from src.core.models.application import Application


def get_by_natural_key(db: Session, planning_authority: str, application_ref: str) -> Application | None:
    return (
        db.query(Application)
        .filter(
            Application.planning_authority == planning_authority,
            Application.application_ref == application_ref,
        )
        .one_or_none()
    )


def search(db: Session, filters: dict, page: int, page_size: int) -> tuple[list[Application], int]:
    query = db.query(Application)

    planning_authority = filters.get("planning_authority")
    if planning_authority:
        query = query.filter(Application.planning_authority == planning_authority)

    planning_status_current = filters.get("planning_status_current")
    if planning_status_current:
        query = query.filter(Application.planning_status_current == planning_status_current)

    application_type = filters.get("application_type")
    if application_type:
        query = query.filter(Application.application_type == application_type)

    date_received_from = filters.get("date_received_from")
    if date_received_from:
        query = query.filter(Application.date_received >= date_received_from)

    date_received_to = filters.get("date_received_to")
    if date_received_to:
        query = query.filter(Application.date_received <= date_received_to)

    q = filters.get("q")
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Application.applicant_name.ilike(pattern),
                Application.site_address.ilike(pattern),
                Application.development_description.ilike(pattern),
            )
        )

    total = query.with_entities(func.count(Application.id)).scalar()

    rows = (
        query.order_by(Application.date_received.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return rows, total
