"""Re-parse stored documents from raw_text. Synthetic notice text only."""

from datetime import date

import pytest
import sqlalchemy as sa

from src.core.db.session import SessionLocal
from src.core.models.decision_document import DecisionDocument
from src.core.models.decision_item import DecisionItem
from src.core.models.dhlgh_application import DHLGHApplication
from src.parsers.decision_notice.extractor import PARSER_VERSION
from src.pipelines.decision_reparse import reparse_documents

AUTH = "REPARSE Test Authority"

NOTICE = (
    "TEST COUNCIL\nNOTIFICATION OF DECISION\nPlanning Reference: TEST/0002\n(CONDITION NO'S 2)\n"
    "Decision: GRANT subject to the conditions set out in the Schedule.\n\n"
    "Schedule Referred To - Planning Reference No. TEST/0002\n\n"
    "1. (a) A maintenance contract for the test system shall be kept in place at all times.\n"
    "Signed and dated copies of the contract shall be made available on request.\n"
    "(b) Imported fill must be free of invasive species.\n"
    "Reason: In the interest of public health.\n\n"
    "2. Services shall be laid underground.\n"
    "REASON In the interest of visual amenity.\n\n"
    "Signed this 01st day of January 2026\nfor Senior Planner\n"
)


def _cleanup():
    s = SessionLocal()
    try:
        s.execute(sa.text("DELETE FROM decision_documents WHERE planning_authority = :a"), {"a": AUTH})
        s.execute(sa.text("DELETE FROM dhlgh_applications WHERE planning_authority = :a"), {"a": AUTH})
        s.commit()
    finally:
        s.close()


@pytest.fixture(autouse=True)
def cleanup():
    _cleanup()
    yield
    _cleanup()


def _seed(session, doc_id: str, raw_text: str, old_items: list[tuple[int, str, str | None]], status="validated", stated=2):
    app = DHLGHApplication(
        planning_authority=AUTH, source_entity="TEST", application_ref=f"RP/{doc_id}",
        development_description="Synthetic", planning_status_current="DECIDED", decision="CONDITIONAL",
        date_received=date(2025, 1, 1), decision_date=date(2025, 3, 1), source_system="dhlgh",
    )
    session.add(app)
    session.flush()
    doc = DecisionDocument(
        planning_authority=AUTH, application_ref=app.application_ref, dhlgh_application_id=app.id,
        council_doc_id=doc_id, doc_type="notification_of_decision", source_url="https://example.invalid/x",
        content_sha256="0" * 64, page_count=1, extraction_method="pdftotext", raw_text=raw_text,
        parser_version="1", status=status, stated_count=stated, target_count=stated,
        parsed_count=len(old_items), failure_reason=None,
    )
    session.add(doc)
    session.flush()
    for n, text, reason in old_items:
        session.add(DecisionItem(document_id=doc.id, item_no=n, kind="condition", text=text, reason_text=reason))
    session.commit()
    return doc.id


V1_ITEMS = [
    (1, "(a) A maintenance contract for the test system shall be kept in place at all times.", None),
    (2, "Services shall be laid underground. REASON In the interest of visual amenity.", None),
]


def _items(session, doc_id):
    return [(i.item_no, i.text, i.reason_text) for i in
            session.query(DecisionItem).filter_by(document_id=doc_id).order_by(DecisionItem.item_no)]


def test_dry_run_reports_changes_without_writing():
    s = SessionLocal()
    try:
        doc_id = _seed(s, "RP1", NOTICE, V1_ITEMS)
        res = reparse_documents(s, authority=AUTH, dry_run=True)
        assert (res.documents_checked, res.documents_changed, res.items_changed) == (1, 1, 2)
        assert res.changes[0].items_changed == [1, 2]
        s.expire_all()
        assert _items(s, doc_id) == V1_ITEMS
        assert s.get(DecisionDocument, doc_id).parser_version == "1"
    finally:
        s.close()


def test_apply_replaces_items_and_sets_parser_version():
    s = SessionLocal()
    try:
        doc_id = _seed(s, "RP2", NOTICE, V1_ITEMS)
        res = reparse_documents(s, authority=AUTH)
        assert res.documents_changed == 1
        s.expire_all()
        items = _items(s, doc_id)
        assert items[0][1].endswith("Imported fill must be free of invasive species.")
        assert "Signed and dated copies of the contract" in items[0][1]
        assert items[0][2] == "In the interest of public health."
        assert items[1] == (2, "Services shall be laid underground.", "In the interest of visual amenity.")
        doc = s.get(DecisionDocument, doc_id)
        assert (doc.status, doc.parsed_count, doc.parser_version) == ("validated", 2, PARSER_VERSION)
    finally:
        s.close()


def test_second_run_changes_nothing():
    s = SessionLocal()
    try:
        _seed(s, "RP3", NOTICE, V1_ITEMS)
        reparse_documents(s, authority=AUTH)
        res = reparse_documents(s, authority=AUTH)
        assert (res.documents_changed, res.documents_unchanged) == (0, 1)
    finally:
        s.close()


def test_unchanged_document_keeps_items_and_gets_new_version():
    s = SessionLocal()
    try:
        current = [
            (1, "(a) A maintenance contract for the test system shall be kept in place at all times. "
                "Signed and dated copies of the contract shall be made available on request. "
                "(b) Imported fill must be free of invasive species.", "In the interest of public health."),
            (2, "Services shall be laid underground.", "In the interest of visual amenity."),
        ]
        doc_id = _seed(s, "RP4", NOTICE, current)
        before_ids = sorted(str(i.id) for i in s.query(DecisionItem).filter_by(document_id=doc_id))
        res = reparse_documents(s, authority=AUTH)
        assert (res.documents_changed, res.documents_unchanged) == (0, 1)
        s.expire_all()
        assert sorted(str(i.id) for i in s.query(DecisionItem).filter_by(document_id=doc_id)) == before_ids
        assert s.get(DecisionDocument, doc_id).parser_version == PARSER_VERSION
    finally:
        s.close()


def test_status_change_is_recorded():
    s = SessionLocal()
    try:
        # stored as validated with 3 items, but the notice states 2 and the parser now finds 2
        doc_id = _seed(s, "RP5", NOTICE.replace("(CONDITION NO'S 2)", "(CONDITION NO'S 3)"), V1_ITEMS, stated=3)
        res = reparse_documents(s, authority=AUTH)
        c = res.changes[0]
        assert (c.old_status, c.new_status) == ("validated", "count_mismatch")
        s.expire_all()
        assert s.get(DecisionDocument, doc_id).status == "count_mismatch"
    finally:
        s.close()
