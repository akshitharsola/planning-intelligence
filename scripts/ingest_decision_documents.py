"""CLI script for ingesting decision documents and items for Galway County planning applications.

Usage:
    python -m scripts.ingest_decision_documents --authority "Galway County Council" --since-year 2023 --limit 100
    python -m scripts.ingest_decision_documents --authority "Galway County Council" --refs 2360654,2260277 --dry-run
"""

import argparse
from datetime import date, datetime
import logging
from pathlib import Path
import sys

# Ensure repository root is on sys.path when script is invoked directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.db.session import SessionLocal
from src.pipelines.decision_documents import ingest_authority
from src.sources.galway.decision_documents import CountyDocFetcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ingest_decision_documents")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Ingest Galway County decision documents and reasons/conditions."
    )
    parser.add_argument(
        "--authority",
        type=str,
        default="Galway County Council",
        help="Planning authority name (default: Galway County Council)",
    )
    parser.add_argument(
        "--from-date",
        type=str,
        default=None,
        help="Filter decision date >= YYYY-MM-DD",
    )
    parser.add_argument(
        "--since-year",
        type=int,
        default=2023,
        help="Filter decision year >= YYYY (default: 2023)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of applications to process",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Sample N applications at random (seeded with --seed)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for sampling (default: 42)",
    )
    parser.add_argument(
        "--refs",
        type=str,
        default=None,
        help="Comma-separated application refs to process (e.g. 2360654,2260277)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and output results without saving to database",
    )
    return parser.parse_args(argv)


def main():
    args = parse_args()

    from_date = None
    if args.from_date:
        from_date = datetime.strptime(args.from_date, "%Y-%m-%d").date()

    refs_list = None
    if args.refs:
        refs_list = [r.strip() for r in args.refs.split(",") if r.strip()]

    session = SessionLocal()
    fetcher = CountyDocFetcher()

    try:
        result = ingest_authority(
            session=session,
            fetcher=fetcher,
            authority=args.authority,
            from_date=from_date,
            since_year=args.since_year,
            limit=args.limit,
            refs=refs_list,
            sample=args.sample,
            seed=args.seed,
            dry_run=args.dry_run,
        )
    finally:
        session.close()

    if result.failures > 0 and result.documents_stored == 0 and result.documents_skipped_unchanged == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

