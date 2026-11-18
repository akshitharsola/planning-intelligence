"""Export decision_documents + decision_items to a gzipped JSONL file.

Usage:
    python scripts/export_decision_data.py [--authority "Galway County Council"] [--output PATH]

Default output: ./data/exports/decision_data_<UTC timestamp>.jsonl.gz (gitignored).
Records are keyed by (planning_authority, council_doc_id) and carry no internal
uuids and no dhlgh_application_id. The file holds extracted council text: share it
privately and NEVER commit it.
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.db.session import SessionLocal
from src.pipelines.decision_data_exchange import export_decision_data

DEFAULT_DIR = Path("data/exports")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--authority", default=None, help="Only export this planning authority")
    parser.add_argument("--output", default=None, help="Output path (.jsonl.gz)")
    return parser.parse_args(argv)


def main(argv=None) -> None:
    args = parse_args(argv)
    if args.output:
        out = Path(args.output)
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = DEFAULT_DIR / f"decision_data_{stamp}.jsonl.gz"

    session = SessionLocal()
    try:
        stats = export_decision_data(session, out, authority=args.authority)
    finally:
        session.close()

    size = out.stat().st_size
    print(f"Wrote {stats.documents} documents, {stats.items} items to {out.resolve()} ({size:,} bytes)")
    print("This file contains extracted council text. Share it privately; never commit it.")


if __name__ == "__main__":
    main()
