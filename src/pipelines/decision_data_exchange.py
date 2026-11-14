"""Export / import decision_documents + decision_items between local databases.

The exchange file is gzipped JSONL, one decision document per line with its items
nested. Records are keyed by (planning_authority, council_doc_id). Internal uuids
(document id, item ids, dhlgh_application_id) are never written: on import the
document is relinked to the local dhlgh_applications row by
(planning_authority, application_ref), or left unlinked if there is none.

The file contains extracted council text. It must never be committed to git.
"""

from dataclasses import dataclass
from datetime import datetime
import gzip
import json
from pathlib import Path
from typing import Iterator, Optional
import uuid

from sqlalchemy.orm import Session, selectinload

from src.core.models.decision_document import DecisionDocument
from src.core.models.decision_item import DecisionItem
from src.core.models.dhlgh_application import DHLGHApplication

FORMAT_VERSION = 1

DOCUMENT_FIELDS = (
    "planning_authority",
    "application_ref",
    "council_doc_id",
    "doc_type",
    "source_url",
    "content_sha256",
    "page_count",
    "extraction_method",
    "raw_text",
    "parser_version",
    "status",
    "stated_count",
    "target_count",
    "parsed_count",
    "failure_reason",
    "fetched_at",
    "extracted_at",
)
DATETIME_FIELDS = ("fetched_at", "extracted_at")
ITEM_FIELDS = ("item_no", "kind", "text", "reason_text")


@dataclass
class ExportStats:
    documents: int = 0
    items: int = 0


@dataclass
class ImportStats:
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    unlinked: int = 0
    items_written: int = 0


def _document_record(doc: DecisionDocument) -> dict:
    rec: dict = {"format": FORMAT_VERSION}
    for f in DOCUMENT_FIELDS:
        value = getattr(doc, f)
        if f in DATETIME_FIELDS and value is not None:
            value = value.isoformat()
        rec[f] = value
    rec["items"] = [
        {f: getattr(item, f) for f in ITEM_FIELDS}
        for item in sorted(doc.items, key=lambda i: i.item_no)
    ]
    return rec


def export_decision_data(
    session: Session, out_path: Path, authority: Optional[str] = None, batch_size: int = 500
) -> ExportStats:
    """Write every stored decision document (optionally one authority) to out_path."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    stats = ExportStats()

    query = session.query(DecisionDocument).options(selectinload(DecisionDocument.items))
    if authority:
        query = query.filter(DecisionDocument.planning_authority == authority)
    query = query.order_by(DecisionDocument.planning_authority, DecisionDocument.council_doc_id)

    with gzip.open(out_path, "wt", encoding="utf-8") as fh:
        offset = 0
        while True:
            batch = query.offset(offset).limit(batch_size).all()
            if not batch:
                break
            for doc in batch:
                rec = _document_record(doc)
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                stats.documents += 1
                stats.items += len(rec["items"])
            offset += batch_size
            for doc in batch:
                session.expunge(doc)  # keep memory flat; cascades to its items
    return stats


def iter_records(path: Path) -> Iterator[dict]:
    with gzip.open(Path(path), "rt", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("format") != FORMAT_VERSION:
                raise ValueError(f"line {line_no}: unsupported format {rec.get('format')!r}")
            yield rec


def _apply_fields(doc: DecisionDocument, rec: dict) -> None:
    for f in DOCUMENT_FIELDS:
        value = rec.get(f)
        if f in DATETIME_FIELDS and value is not None:
            value = datetime.fromisoformat(value)
        setattr(doc, f, value)


def _add_items(session: Session, doc: DecisionDocument, rec: dict) -> int:
    for item in rec.get("items", []):
        session.add(DecisionItem(document_id=doc.id, **{f: item.get(f) for f in ITEM_FIELDS}))
    return len(rec.get("items", []))


def import_decision_data(session: Session, path: Path, commit_every: int = 200) -> ImportStats:
    """Idempotent upsert of an exchange file on (planning_authority, council_doc_id).

    - New document: inserted with its items.
    - Same content_sha256: left as is (only the application link is refreshed).
    - Different content_sha256: fields updated and items replaced.
    """
    stats = ImportStats()
    app_ids: dict[tuple[str, str], Optional[uuid.UUID]] = {}

    def local_app_id(authority: str, ref: str) -> Optional[uuid.UUID]:
        key = (authority, ref)
        if key not in app_ids:
            app_ids[key] = (
                session.query(DHLGHApplication.id)
                .filter_by(planning_authority=authority, application_ref=ref)
                .scalar()
            )
        return app_ids[key]

    pending = 0
    for rec in iter_records(path):
        authority, doc_id = rec["planning_authority"], rec["council_doc_id"]
        link_id = local_app_id(authority, rec["application_ref"])
        if link_id is None:
            stats.unlinked += 1

        existing = (
            session.query(DecisionDocument)
            .filter_by(planning_authority=authority, council_doc_id=doc_id)
            .one_or_none()
        )
        if existing is None:
            doc = DecisionDocument()
            _apply_fields(doc, rec)
            doc.dhlgh_application_id = link_id
            session.add(doc)
            session.flush()
            stats.items_written += _add_items(session, doc, rec)
            stats.inserted += 1
        elif existing.content_sha256 == rec["content_sha256"]:
            if existing.dhlgh_application_id != link_id:
                existing.dhlgh_application_id = link_id
            stats.unchanged += 1
        else:
            existing.items.clear()
            session.flush()
            _apply_fields(existing, rec)
            existing.dhlgh_application_id = link_id
            stats.items_written += _add_items(session, existing, rec)
            stats.updated += 1

        pending += 1
        if pending >= commit_every:
            session.commit()
            pending = 0
    session.commit()
    return stats
