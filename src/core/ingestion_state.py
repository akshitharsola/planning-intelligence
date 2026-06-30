"""
Persisted incremental-ingestion state: County's OBJECTID watermark and
City's per-file ingestion tracking, so CLI re-runs don't reprocess
already-ingested data. Backed by ingestion_state and ingested_files
(migration 0002).
"""

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_watermark(session: Session, region: str) -> str | None:
    row = session.execute(
        text("SELECT watermark FROM ingestion_state WHERE region = :region"),
        {"region": region},
    ).first()
    return row[0] if row else None


def set_watermark(session: Session, region: str, watermark: str) -> None:
    session.execute(
        text(
            """
            INSERT INTO ingestion_state (region, watermark, updated_at)
            VALUES (:region, :watermark, now())
            ON CONFLICT (region) DO UPDATE
                SET watermark = EXCLUDED.watermark, updated_at = now()
            """
        ),
        {"region": region, "watermark": watermark},
    )


def is_file_ingested(session: Session, region: str, file_id: str) -> bool:
    row = session.execute(
        text(
            "SELECT 1 FROM ingested_files WHERE region = :region AND file_id = :file_id"
        ),
        {"region": region, "file_id": file_id},
    ).first()
    return row is not None


def mark_file_ingested(session: Session, region: str, file_id: str) -> None:
    session.execute(
        text(
            """
            INSERT INTO ingested_files (region, file_id, ingested_at)
            VALUES (:region, :file_id, now())
            ON CONFLICT (region, file_id) DO NOTHING
            """
        ),
        {"region": region, "file_id": file_id},
    )
