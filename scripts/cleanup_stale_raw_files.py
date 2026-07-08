"""
Deletes staged Galway City PDFs from data/galway/city/raw/ once they are
older than max_age_days AND confirmed ingested via ingested_files. Never
deletes a stale file that failed to ingest, so the existing self-healing
retry in ingest_galway_city.py still has the file to retry against. See
docs/superpowers/specs/2026-07-08-weekly-scheduler-and-staging-design.md.
"""

import argparse
import logging
import time
from pathlib import Path

from src.core.db.session import SessionLocal
from src.core.ingestion_state import is_file_ingested

logger = logging.getLogger(__name__)

DEFAULT_RAW_DIR = Path("data/galway/city/raw")
DEFAULT_REGION = "galway_city"
DEFAULT_MAX_AGE_DAYS = 30


def cleanup_stale_raw_files(
    raw_dir: Path = DEFAULT_RAW_DIR,
    region: str = DEFAULT_REGION,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
    dry_run: bool = False,
) -> dict:
    result = {"deleted": [], "skipped_not_ingested": [], "skipped_too_new": []}

    if not raw_dir.exists():
        return result

    session = SessionLocal()
    try:
        now = time.time()
        cutoff_seconds = max_age_days * 86400

        for pdf_path in sorted(raw_dir.rglob("*.pdf")):
            age_seconds = now - pdf_path.stat().st_mtime
            if age_seconds < cutoff_seconds:
                result["skipped_too_new"].append(pdf_path.name)
                continue

            if not is_file_ingested(session, region, pdf_path.name):
                result["skipped_not_ingested"].append(pdf_path.name)
                continue

            result["deleted"].append(pdf_path.name)
            if not dry_run:
                pdf_path.unlink()
    finally:
        session.close()

    if not dry_run:
        _prune_empty_dirs(raw_dir)

    return result


def _prune_empty_dirs(root: Path) -> None:
    for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean up stale, ingested City raw PDFs.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    result = cleanup_stale_raw_files(dry_run=args.dry_run)
    logger.info(
        "cleanup complete: deleted=%d skipped_not_ingested=%d skipped_too_new=%d",
        len(result["deleted"]),
        len(result["skipped_not_ingested"]),
        len(result["skipped_too_new"]),
    )


if __name__ == "__main__":
    main()
