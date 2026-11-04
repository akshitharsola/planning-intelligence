import uuid
import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from src.core.db.session import SessionLocal
from src.core.models.decision_document import DecisionDocument
from src.core.models.decision_item import DecisionItem


def _cleanup():
    session = SessionLocal()
    try:
        session.execute(
            sa.text("DELETE FROM decision_documents WHERE application_ref LIKE 'TEST_TBL/%'")
        )
        session.commit()
    finally:
        session.close()


@pytest.fixture(autouse=True)
def cleanup_after_test():
    _cleanup()
    yield
    _cleanup()


def test_insert_document_with_items_roundtrip():
    session = SessionLocal()
    try:
        doc = DecisionDocument(
            planning_authority="Galway County Council",
            application_ref="TEST_TBL/001",
            council_doc_id="DOC_1001",
            doc_type="notification_of_decision",
            source_url="https://example.com/doc1001.pdf",
            content_sha256="abc123sha",
            page_count=2,
            extraction_method="pdftotext",
            raw_text="Full text of notice",
            parser_version="1",
            status="validated",
            stated_count=2,
            target_count=2,
            parsed_count=2,
        )
        item1 = DecisionItem(
            document=doc,
            item_no=1,
            kind="condition",
            text="The development shall be carried out in accordance with plans submitted.",
            reason_text="In the interest of proper planning.",
        )
        item2 = DecisionItem(
            document=doc,
            item_no=2,
            kind="condition",
            text="A boundary wall shall be erected prior to occupation.",
            reason_text="In the interest of residential amenity.",
        )
        session.add(doc)
        session.add_all([item1, item2])
        session.commit()

        # Query back
        loaded_doc = session.query(DecisionDocument).filter_by(council_doc_id="DOC_1001").one()
        assert loaded_doc.application_ref == "TEST_TBL/001"
        assert len(loaded_doc.items) == 2
        assert loaded_doc.items[0].item_no == 1
        assert loaded_doc.items[1].item_no == 2
    finally:
        session.close()


def test_duplicate_council_doc_id_per_authority_rejected():
    session = SessionLocal()
    try:
        doc1 = DecisionDocument(
            planning_authority="Galway County Council",
            application_ref="TEST_TBL/002",
            council_doc_id="DOC_DUP_1",
            doc_type="notification_of_decision",
            source_url="https://example.com/doc1.pdf",
            content_sha256="sha1",
            raw_text="Notice 1",
            parser_version="1",
            status="validated",
            parsed_count=0,
        )
        session.add(doc1)
        session.commit()

        doc2 = DecisionDocument(
            planning_authority="Galway County Council",
            application_ref="TEST_TBL/003",
            council_doc_id="DOC_DUP_1",
            doc_type="notification_of_decision",
            source_url="https://example.com/doc2.pdf",
            content_sha256="sha2",
            raw_text="Notice 2",
            parser_version="1",
            status="validated",
            parsed_count=0,
        )
        session.add(doc2)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.close()


def test_same_council_doc_id_other_authority_allowed():
    session = SessionLocal()
    try:
        doc1 = DecisionDocument(
            planning_authority="Galway County Council",
            application_ref="TEST_TBL/004",
            council_doc_id="DOC_SHARED_1",
            doc_type="notification_of_decision",
            source_url="https://example.com/county.pdf",
            content_sha256="sha1",
            raw_text="County Notice",
            parser_version="1",
            status="validated",
            parsed_count=0,
        )
        doc2 = DecisionDocument(
            planning_authority="Galway City Council",
            application_ref="TEST_TBL/004",
            council_doc_id="DOC_SHARED_1",
            doc_type="notification_of_decision",
            source_url="https://example.com/city.pdf",
            content_sha256="sha2",
            raw_text="City Notice",
            parser_version="1",
            status="validated",
            parsed_count=0,
        )
        session.add_all([doc1, doc2])
        session.commit()

        docs = (
            session.query(DecisionDocument)
            .filter_by(council_doc_id="DOC_SHARED_1")
            .all()
        )
        assert len(docs) == 2
        authorities = {d.planning_authority for d in docs}
        assert authorities == {"Galway County Council", "Galway City Council"}
    finally:
        session.close()


def test_duplicate_item_no_rejected():
    session = SessionLocal()
    try:
        doc = DecisionDocument(
            planning_authority="Galway County Council",
            application_ref="TEST_TBL/005",
            council_doc_id="DOC_ITEM_DUP",
            doc_type="notification_of_decision",
            source_url="https://example.com/doc.pdf",
            content_sha256="sha1",
            raw_text="Notice",
            parser_version="1",
            status="validated",
            parsed_count=2,
        )
        item1 = DecisionItem(
            document=doc,
            item_no=1,
            kind="condition",
            text="First item",
        )
        item2 = DecisionItem(
            document=doc,
            item_no=1,
            kind="condition",
            text="Duplicate number item",
        )
        session.add(doc)
        session.add_all([item1, item2])
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.close()


def test_delete_document_cascades_items():
    session = SessionLocal()
    try:
        doc = DecisionDocument(
            planning_authority="Galway County Council",
            application_ref="TEST_TBL/006",
            council_doc_id="DOC_CASCADE",
            doc_type="notification_of_decision",
            source_url="https://example.com/doc.pdf",
            content_sha256="sha1",
            raw_text="Notice",
            parser_version="1",
            status="validated",
            parsed_count=1,
        )
        item = DecisionItem(
            document=doc,
            item_no=1,
            kind="condition",
            text="Item to be cascaded",
        )
        session.add(doc)
        session.add(item)
        session.commit()
        doc_id = doc.id
        item_id = item.id

        # Delete document via SQL to verify DB-level ON DELETE CASCADE
        session.execute(
            sa.text("DELETE FROM decision_documents WHERE id = :id"),
            {"id": doc_id},
        )
        session.commit()

        items_remaining = session.query(DecisionItem).filter_by(id=item_id).all()
        assert len(items_remaining) == 0
    finally:
        session.close()


def test_search_vector_matches_word():
    session = SessionLocal()
    try:
        doc = DecisionDocument(
            planning_authority="Galway County Council",
            application_ref="TEST_TBL/007",
            council_doc_id="DOC_TSVECTOR",
            doc_type="notification_of_decision",
            source_url="https://example.com/doc.pdf",
            content_sha256="sha1",
            raw_text="Notice",
            parser_version="1",
            status="validated",
            parsed_count=1,
        )
        item = DecisionItem(
            document=doc,
            item_no=1,
            kind="condition",
            text="The existing stone boundary wall shall be retained in full.",
            reason_text="In the interest of residential amenity and architectural heritage.",
        )
        session.add(doc)
        session.add(item)
        session.commit()

        # Query using tsvector @@ to_tsquery for word in condition text
        matched_text = (
            session.query(DecisionItem)
            .filter(
                DecisionItem.document_id == doc.id,
                sa.text("decision_items.search_vector @@ to_tsquery('english', 'wall')"),
            )
            .all()
        )
        assert len(matched_text) == 1
        assert matched_text[0].id == item.id

        # Query using tsvector @@ to_tsquery for word in reason_text
        matched_reason = (
            session.query(DecisionItem)
            .filter(
                DecisionItem.document_id == doc.id,
                sa.text("decision_items.search_vector @@ to_tsquery('english', 'heritage')"),
            )
            .all()
        )
        assert len(matched_reason) == 1
        assert matched_reason[0].id == item.id

        unmatched = (
            session.query(DecisionItem)
            .filter(
                DecisionItem.document_id == doc.id,
                sa.text("decision_items.search_vector @@ to_tsquery('english', 'skyscraper')"),
            )
            .all()
        )
        assert len(unmatched) == 0
    finally:
        session.close()


def test_invalid_status_rejected():
    session = SessionLocal()
    try:
        doc = DecisionDocument(
            planning_authority="Galway County Council",
            application_ref="TEST_TBL/008",
            council_doc_id="DOC_INVALID_STATUS",
            doc_type="notification_of_decision",
            source_url="https://example.com/doc.pdf",
            content_sha256="sha1",
            raw_text="Notice",
            parser_version="1",
            status="some_invented_status",
            parsed_count=0,
        )
        session.add(doc)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.close()


def test_invalid_kind_rejected():
    session = SessionLocal()
    try:
        doc = DecisionDocument(
            planning_authority="Galway County Council",
            application_ref="TEST_TBL/009",
            council_doc_id="DOC_INVALID_KIND",
            doc_type="notification_of_decision",
            source_url="https://example.com/doc.pdf",
            content_sha256="sha1",
            raw_text="Notice",
            parser_version="1",
            status="validated",
            parsed_count=1,
        )
        item = DecisionItem(
            document=doc,
            item_no=1,
            kind="not_a_valid_kind",
            text="Invalid kind item",
        )
        session.add(doc)
        session.add(item)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.close()

