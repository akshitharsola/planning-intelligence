"""Re-parse stored decision documents with the current parser. Makes no network requests.

Usage:
    python scripts/reparse_decision_documents.py --dry-run [--report logs/reparse.tsv]
    python scripts/reparse_decision_documents.py [--authority "Galway County Council"] [--report PATH]

--dry-run lists what would change without writing. The report lists refs, document ids,
statuses and changed item numbers only (no notice text); keep it out of git anyway.
"""

import argparse
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.db.session import SessionLocal
from src.parsers.decision_notice.extractor import PARSER_VERSION
from src.pipelines.decision_reparse import reparse_documents


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--authority", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", default=None, help="Write a TSV of changed documents")
    return parser.parse_args(argv)


def main(argv=None) -> None:
    args = parse_args(argv)
    session = SessionLocal()
    try:
        res = reparse_documents(session, authority=args.authority, dry_run=args.dry_run)
    finally:
        session.close()

    verb = "would change" if args.dry_run else "changed"
    print(f"parser_version={PARSER_VERSION} dry_run={args.dry_run}")
    print(f"documents checked={res.documents_checked} unchanged={res.documents_unchanged} "
          f"{verb}={res.documents_changed} items {verb}={res.items_changed}")
    transitions = Counter((c.old_status, c.new_status) for c in res.changes)
    for (old, new), n in sorted(transitions.items()):
        print(f"  {old} -> {new}: {n}")

    if args.report:
        out = Path(args.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as fh:
            fh.write("application_ref\tcouncil_doc_id\tdoc_type\told_status\tnew_status\told_parsed\tnew_parsed\titems_changed\n")
            for c in res.changes:
                fh.write(f"{c.application_ref}\t{c.council_doc_id}\t{c.doc_type}\t{c.old_status}\t{c.new_status}\t"
                         f"{c.old_parsed_count}\t{c.new_parsed_count}\t{','.join(map(str, c.items_changed))}\n")
        print(f"report: {out}")


if __name__ == "__main__":
    main()
