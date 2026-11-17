"""Re-parse stored decision documents from their saved raw_text. No network access.

Used when the extractor improves: every stored document is parsed again with the
current PARSER_VERSION using the same inputs as the original ingest (authority,
the linked application's decision, and the ePlanning count when the notice states
none). Documents whose result changed get new status/counts and replaced items.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session, selectinload

from src.core.models.decision_document import DecisionDocument
from src.core.models.decision_item import DecisionItem
from src.parsers.decision_notice.extractor import PARSER_VERSION, ParsedNotice, parse_notice

ITEM_STATUSES = ("validated", "count_mismatch", "unverified")


@dataclass
class DocumentChange:
    application_ref: str
    council_doc_id: str
    doc_type: str
    old_status: str
    new_status: str
    old_parsed_count: int
    new_parsed_count: int
    items_changed: list[int]


@dataclass
class ReparseResult:
    documents_checked: int = 0
    documents_unchanged: int = 0
    documents_changed: int = 0
    items_changed: int = 0
    changes: list[DocumentChange] = field(default_factory=list)


def _item_kind(parsed: ParsedNotice, decision: Optional[str]) -> str:
    default_kind = "refusal_reason" if "REFU" in (decision or "").upper() else "condition"
    return parsed.kind or default_kind


def _new_items(parsed: ParsedNotice, decision: Optional[str]) -> list[tuple[int, str, str, Optional[str]]]:
    if parsed.status not in ITEM_STATUSES:
        return []
    kind = _item_kind(parsed, decision)
    return [(it.n, kind, it.text, it.reason_text) for it in parsed.items]


def reparse_documents(
    session: Session,
    authority: Optional[str] = None,
    dry_run: bool = False,
    commit_every: int = 200,
) -> ReparseResult:
    result = ReparseResult()
    id_query = session.query(DecisionDocument.id).filter(DecisionDocument.extraction_method == "pdftotext")
    if authority:
        id_query = id_query.filter(DecisionDocument.planning_authority == authority)
    doc_ids = [
        r[0] for r in id_query.order_by(DecisionDocument.planning_authority, DecisionDocument.council_doc_id)
    ]

    def batches():
        for start in range(0, len(doc_ids), commit_every):
            chunk = doc_ids[start:start + commit_every]
            docs = (
                session.query(DecisionDocument)
                .options(selectinload(DecisionDocument.items), selectinload(DecisionDocument.dhlgh_application))
                .filter(DecisionDocument.id.in_(chunk))
                .order_by(DecisionDocument.planning_authority, DecisionDocument.council_doc_id)
                .all()
            )
            yield from docs
            if not dry_run:
                session.commit()
            session.expunge_all()

    for doc in batches():
        result.documents_checked += 1
        decision = doc.dhlgh_application.decision if doc.dhlgh_application else None
        eplan_count = doc.target_count if doc.stated_count is None else None
        parsed = parse_notice(doc.raw_text, authority=doc.planning_authority, eplan_count=eplan_count, decision=decision)

        old_items = {i.item_no: (i.item_no, i.kind, i.text, i.reason_text) for i in doc.items}
        new_items = {t[0]: t for t in _new_items(parsed, decision)}
        changed_nos = sorted(n for n in set(old_items) | set(new_items) if old_items.get(n) != new_items.get(n))
        fields_changed = (
            doc.status != parsed.status
            or doc.stated_count != parsed.stated_count
            or doc.target_count != parsed.target_count
            or doc.parsed_count != len(parsed.items)
            or doc.failure_reason != parsed.failure_reason
        )

        if not changed_nos and not fields_changed:
            result.documents_unchanged += 1
            if not dry_run and doc.parser_version != PARSER_VERSION:
                doc.parser_version = PARSER_VERSION
        else:
            result.documents_changed += 1
            result.items_changed += len(changed_nos)
            result.changes.append(
                DocumentChange(
                    application_ref=doc.application_ref,
                    council_doc_id=doc.council_doc_id,
                    doc_type=doc.doc_type,
                    old_status=doc.status,
                    new_status=parsed.status,
                    old_parsed_count=doc.parsed_count,
                    new_parsed_count=len(parsed.items),
                    items_changed=changed_nos,
                )
            )
            if not dry_run:
                doc.status = parsed.status
                doc.stated_count = parsed.stated_count
                doc.target_count = parsed.target_count
                doc.parsed_count = len(parsed.items)
                doc.failure_reason = parsed.failure_reason
                doc.parser_version = PARSER_VERSION
                doc.extracted_at = datetime.now()
                doc.items.clear()
                session.flush()
                for n, kind, text, reason in new_items.values():
                    session.add(DecisionItem(document_id=doc.id, item_no=n, kind=kind, text=text, reason_text=reason))

    if not dry_run:
        session.commit()
    else:
        session.rollback()
    return result
