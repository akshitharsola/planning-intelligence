"""
Publish stage: commits the session and records ingestion metrics
(spec section 3 — src/monitoring/metrics.py, populated in Task 8).
"""

from sqlalchemy.orm import Session

from src.monitoring.metrics import record_ingestion_run


def publish(session: Session, region: str, rows_ingested: int, parse_errors: int) -> None:
    session.commit()
    record_ingestion_run(region=region, rows_ingested=rows_ingested, parse_errors=parse_errors)
