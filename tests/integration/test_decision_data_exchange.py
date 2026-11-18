"""Round-trip tests for exporting/importing decision data between local databases.

All text here is synthetic. No real notice text, applicant names, addresses or eircodes.
"""

from datetime import date, datetime
import gzip
import json

import pytest
import sqlalchemy as sa

from src.core.db.session import SessionLocal
from src.core.models.decision_document import DecisionDocument
from src.core.models.decision_item import DecisionItem
from src.core.models.dhlgh_application import DHLGHApplication
from src.pipelines.decision_data_exchange import export_decision_data, import_decision_data

AUTH = "XCHG Test Authority"


def _cleanup():
    session = SessionLocal()
    try:
        session.execute(sa.text("DELETE FROM decision_documents WHERE planning_authority = :a"), {"a": AUTH})
        session.execute(sa.text("DELETE FROM dhlgh_applications WHERE planning_authority = :a"), {"a": AUTH})
        session.commit()
    finally:
        session.close()


@pytest.fixture(autouse=True)
def cleanup():
    _cleanup()
    yield
    _cleanup()


@pytest.fixture
def session():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


def _seed_app(session, ref: str) -> DHLGHApplication:
    app = DHLGHApplication(
        planning_authority=AUTH,
        source_entity="TEST",
        application_ref=ref,
        development_description="Synthetic development",
        planning_status_current="DECIDED",
        decision="CONDITIONAL",
        date_received=date(2025, 1, 1),
        decision_date=date(2025, 3, 1),
        source_system="dhlgh",
    )
    session.add(app)
    session.commit()
    return app


def _seed_doc(session, app, doc_id: str, n_items: int = 2, sha: str = "a" * 64) -> DecisionDocument:
    doc = DecisionDocument(
        planning_authority=AUTH,
        application_ref=app.application_ref,
        dhlgh_application_id=app.id,
        council_doc_id=doc_id,
        doc_type="notification_of_decision",
        source_url=f"https://example.invalid/ViewPDF.aspx?ref={doc_id}",
        content_sha256=sha,
        page_count=3,
        extraction_method="pdftotext",
        raw_text="SYNTHETIC NOTICE TEXT",
        parser_version="1",
        status="validated",
        stated_count=n_items,
        target_count=n_items,
        parsed_count=n_items,
        failure_reason=None,
        fetched_at=datetime(2026, 1, 2, 3, 4, 5),
        extracted_at=datetime(2026, 1, 2, 3, 4, 6),
    )
    session.add(doc)
    session.flush()
    for i in range(1, n_items + 1):
        session.add(
            DecisionItem(
                document_id=doc.id,
                item_no=i,
                kind="condition",
                text=f"Synthetic condition {i}.",
                reason_text=f"Synthetic reason {i}." if i % 2 else None,
            )
        )
    session.commit()
    return doc


def _read(path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _write(path, records):
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


def _snapshot(session):
    docs = (
        session.query(DecisionDocument)
        .filter_by(planning_authority=AUTH)
        .order_by(DecisionDocument.council_doc_id)
        .all()
    )
    return [
        (
            d.application_ref, d.council_doc_id, d.doc_type, d.source_url, d.content_sha256,
            d.page_count, d.extraction_method, d.raw_text, d.parser_version, d.status,
            d.stated_count, d.target_count, d.parsed_count, d.failure_reason,
            d.fetched_at, d.extracted_at,
            sorted((i.item_no, i.kind, i.text, i.reason_text) for i in d.items),
        )
        for d in docs
    ]


def test_export_has_no_internal_ids(session, tmp_path):
    app = _seed_app(session, "XCHG/1")
    _seed_doc(session, app, "X1")
    out = tmp_path / "out.jsonl.gz"
    stats = export_decision_data(session, out, authority=AUTH)
    assert stats.documents == 1
    assert stats.items == 2

    raw = gzip.open(out, "rt", encoding="utf-8").read()
    assert str(app.id) not in raw
    rec = _read(out)[0]
    assert "id" not in rec
    assert "dhlgh_application_id" not in rec
    assert (rec["planning_authority"], rec["council_doc_id"]) == (AUTH, "X1")
    for item in rec["items"]:
        assert set(item) == {"item_no", "kind", "text", "reason_text"}


def test_round_trip_restores_documents_and_items(session, tmp_path):
    app = _seed_app(session, "XCHG/RT")
    _seed_doc(session, app, "RT1", n_items=3)
    _seed_doc(session, app, "RT2", n_items=1, sha="b" * 64)
    before = _snapshot(session)
    out = tmp_path / "rt.jsonl.gz"
    export_decision_data(session, out, authority=AUTH)

    session.execute(sa.text("DELETE FROM decision_documents WHERE planning_authority = :a"), {"a": AUTH})
    session.commit()

    res = import_decision_data(session, out)
    assert (res.inserted, res.updated, res.unchanged) == (2, 0, 0)
    session.expire_all()
    assert _snapshot(session) == before
    linked = session.query(DecisionDocument).filter_by(planning_authority=AUTH).all()
    assert all(d.dhlgh_application_id == app.id for d in linked)


def test_import_is_idempotent(session, tmp_path):
    app = _seed_app(session, "XCHG/IDEM")
    _seed_doc(session, app, "ID1")
    out = tmp_path / "idem.jsonl.gz"
    export_decision_data(session, out, authority=AUTH)
    session.execute(sa.text("DELETE FROM decision_documents WHERE planning_authority = :a"), {"a": AUTH})
    session.commit()

    import_decision_data(session, out)
    session.expire_all()
    item_ids = sorted(str(i.id) for d in session.query(DecisionDocument).filter_by(planning_authority=AUTH) for i in d.items)

    res2 = import_decision_data(session, out)
    assert (res2.inserted, res2.updated, res2.unchanged) == (0, 0, 1)
    session.expire_all()
    assert session.query(DecisionDocument).filter_by(planning_authority=AUTH).count() == 1
    item_ids_after = sorted(str(i.id) for d in session.query(DecisionDocument).filter_by(planning_authority=AUTH) for i in d.items)
    assert item_ids_after == item_ids


def test_import_relinks_to_local_application_by_authority_and_ref(session, tmp_path):
    app = _seed_app(session, "XCHG/RELINK")
    _seed_doc(session, app, "RL1")
    out = tmp_path / "relink.jsonl.gz"
    export_decision_data(session, out, authority=AUTH)
    old_id = app.id

    # Simulate another machine: same (authority, ref) but a different internal uuid.
    session.execute(sa.text("DELETE FROM decision_documents WHERE planning_authority = :a"), {"a": AUTH})
    session.execute(sa.text("DELETE FROM dhlgh_applications WHERE planning_authority = :a"), {"a": AUTH})
    session.commit()
    new_app = _seed_app(session, "XCHG/RELINK")
    assert new_app.id != old_id

    import_decision_data(session, out)
    doc = session.query(DecisionDocument).filter_by(planning_authority=AUTH, council_doc_id="RL1").one()
    assert doc.dhlgh_application_id == new_app.id


def test_document_without_matching_application_imports_with_null_link(session, tmp_path):
    app = _seed_app(session, "XCHG/ORPHAN")
    _seed_doc(session, app, "OR1")
    out = tmp_path / "orphan.jsonl.gz"
    export_decision_data(session, out, authority=AUTH)
    session.execute(sa.text("DELETE FROM decision_documents WHERE planning_authority = :a"), {"a": AUTH})
    session.execute(sa.text("DELETE FROM dhlgh_applications WHERE planning_authority = :a"), {"a": AUTH})
    session.commit()

    res = import_decision_data(session, out)
    assert res.inserted == 1
    assert res.unlinked == 1
    doc = session.query(DecisionDocument).filter_by(planning_authority=AUTH, council_doc_id="OR1").one()
    assert doc.dhlgh_application_id is None
    assert len(doc.items) == 2


def test_changed_hash_replaces_items(session, tmp_path):
    app = _seed_app(session, "XCHG/CHG")
    _seed_doc(session, app, "CH1", n_items=2)
    out = tmp_path / "chg.jsonl.gz"
    export_decision_data(session, out, authority=AUTH)
    rec = _read(out)[0]

    rec["content_sha256"] = "c" * 64
    rec["parsed_count"] = rec["stated_count"] = rec["target_count"] = 3
    rec["items"] = [
        {"item_no": n, "kind": "condition", "text": f"Replaced condition {n}.", "reason_text": None}
        for n in (1, 2, 3)
    ]
    changed = tmp_path / "changed.jsonl.gz"
    _write(changed, [rec])

    res = import_decision_data(session, changed)
    assert (res.inserted, res.updated, res.unchanged) == (0, 1, 0)
    session.expire_all()
    doc = session.query(DecisionDocument).filter_by(planning_authority=AUTH, council_doc_id="CH1").one()
    assert doc.content_sha256 == "c" * 64
    assert sorted(i.text for i in doc.items) == [f"Replaced condition {n}." for n in (1, 2, 3)]



def test_cli_scripts_round_trip(session, tmp_path, capsys):
    from scripts.export_decision_data import main as export_main
    from scripts.import_decision_data import main as import_main

    app = _seed_app(session, "XCHG/CLI")
    _seed_doc(session, app, "CLI1")
    out = tmp_path / "cli.jsonl.gz"
    export_main(["--authority", AUTH, "--output", str(out)])
    assert "Wrote 1 documents, 2 items" in capsys.readouterr().out

    session.execute(sa.text("DELETE FROM decision_documents WHERE planning_authority = :a"), {"a": AUTH})
    session.commit()
    import_main([str(out)])
    assert "inserted=1 updated=0 unchanged=0 items_written=2 unlinked=0" in capsys.readouterr().out
    import_main([str(out)])
    assert "inserted=0 updated=0 unchanged=1" in capsys.readouterr().out


def test_newer_parser_version_with_same_hash_replaces_items(session, tmp_path):
    app = _seed_app(session, "XCHG/PV")
    _seed_doc(session, app, "PV1", n_items=2)
    out = tmp_path / "pv.jsonl.gz"
    export_decision_data(session, out, authority=AUTH)
    rec = _read(out)[0]

    rec["parser_version"] = "2"  # same PDF (same content_sha256), re-parsed
    rec["items"][0]["text"] = "Synthetic condition 1, now complete."
    newer = tmp_path / "pv2.jsonl.gz"
    _write(newer, [rec])

    res = import_decision_data(session, newer)
    assert (res.inserted, res.updated, res.unchanged) == (0, 1, 0)
    session.expire_all()
    doc = session.query(DecisionDocument).filter_by(planning_authority=AUTH, council_doc_id="PV1").one()
    assert doc.parser_version == "2"
    assert sorted(i.text for i in doc.items)[0] == "Synthetic condition 1, now complete."

    res2 = import_decision_data(session, newer)
    assert (res2.updated, res2.unchanged) == (0, 1)
