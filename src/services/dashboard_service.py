from datetime import date, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.core.models.application import Application


def get_summary(db: Session) -> dict:
    row = db.query(
        func.count(Application.id),
        func.count(func.distinct(Application.planning_authority)),
        func.min(Application.date_received),
        func.max(Application.date_received),
        func.max(Application.source_ingested_at),
    ).one()
    total, distinct_authorities, earliest, latest, latest_ingested = row
    return {
        "total_applications": total,
        "distinct_authorities": distinct_authorities,
        "earliest_received": earliest,
        "latest_received": latest,
        "latest_ingested_at": latest_ingested,
    }


def get_monthly_counts(db: Session) -> list[dict]:
    month_expr = func.to_char(Application.date_received, "YYYY-MM")
    rows = (
        db.query(month_expr.label("label"), func.count(Application.id).label("value"))
        .group_by(month_expr)
        .order_by(month_expr)
        .all()
    )
    return [{"label": r.label, "value": r.value} for r in rows]


def get_status_breakdown(db: Session) -> list[dict]:
    rows = (
        db.query(
            Application.planning_status_current.label("label"),
            func.count(Application.id).label("value"),
        )
        .group_by(Application.planning_status_current)
        .order_by(func.count(Application.id).desc())
        .all()
    )
    return [{"label": r.label, "value": r.value} for r in rows]


def get_type_breakdown(db: Session) -> list[dict]:
    rows = (
        db.query(
            Application.application_type.label("label"),
            func.count(Application.id).label("value"),
        )
        .group_by(Application.application_type)
        .order_by(func.count(Application.id).desc())
        .all()
    )
    return [{"label": r.label, "value": r.value} for r in rows]


def get_distinct_authorities(db: Session) -> list[str]:
    rows = (
        db.query(Application.planning_authority)
        .distinct()
        .order_by(Application.planning_authority)
        .all()
    )
    return [r[0] for r in rows]
