"""Import a decision-data export (gzipped JSONL) into the local database.

Usage:
    python scripts/import_decision_data.py PATH

Idempotent upsert on (planning_authority, council_doc_id). Each document is
relinked to the local dhlgh_applications row by (planning_authority,
application_ref); with no match it is imported with a null link. Items are
replaced only when content_sha256 or parser_version differs
(so a re-parsed export updates an earlier import). Run scripts/ingest_dhlgh.py first so
the links resolve.
"""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.db.session import SessionLocal
from src.pipelines.decision_data_exchange import import_decision_data


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("path", help="Export file (.jsonl.gz)")
    return parser.parse_args(argv)


def main(argv=None) -> None:
    args = parse_args(argv)
    session = SessionLocal()
    try:
        stats = import_decision_data(session, Path(args.path))
    finally:
        session.close()
    print(
        f"inserted={stats.inserted} updated={stats.updated} unchanged={stats.unchanged} "
        f"items_written={stats.items_written} unlinked={stats.unlinked}"
    )


if __name__ == "__main__":
    main()
