"""
One-off backfill: populate applications.eircode for existing rows by
re-running the same extract_eircode() regex used during normalization
against development_description. Safe to re-run (idempotent — only ever
sets eircode, never clears a value that was already correctly set by a
newer ingest).
"""

import logging

from sqlalchemy import select

from src.core.db.session import SessionLocal
from src.core.models.application import Application
from src.core.normalization.location import extract_eircode

logger = logging.getLogger(__name__)


def run_backfill(dry_run: bool = False) -> dict:
    session = SessionLocal()
    try:
        rows = session.scalars(
            select(Application).where(Application.eircode.is_(None))
        ).all()

        updated = 0
        for application in rows:
            eircode = extract_eircode(application.development_description or "")
            if eircode:
                if not dry_run:
                    application.eircode = eircode
                updated += 1

        if not dry_run:
            session.commit()

        logger.info(
            "Eircode backfill complete: scanned=%d updated=%d dry_run=%s",
            len(rows), updated, dry_run,
        )
        return {"scanned": len(rows), "updated": updated}
    finally:
        session.close()


def main() -> None:
    import argparse

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Backfill eircode for existing applications.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = run_backfill(dry_run=args.dry_run)
    print(result)


if __name__ == "__main__":
    main()
