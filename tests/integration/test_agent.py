"""Agent answers from the DB only. Synthetic applications and notice text."""

from datetime import date

import pytest
import sqlalchemy as sa

from src.agent.agent import NOT_IN_RECORDS, answer_question
from src.core.db.session import SessionLocal, engine
from src.core.models.decision_document import DecisionDocument
from src.core.models.decision_item import DecisionItem
from src.core.models.dhlgh_application import DHLGHApplication

COUNTY, CITY = "Galway County Council", "Galway City Council"
REFS = ("99999901", "99999902", "99999903", "99999904")


def _cleanup():
    s = SessionLocal()
    try:
        s.execute(sa.text("DELETE FROM decision_documents WHERE application_ref IN :r").bindparams(sa.bindparam("r", expanding=True)), {"r": list(REFS)})
        s.execute(sa.text("DELETE FROM dhlgh_applications WHERE application_ref IN :r").bindparams(sa.bindparam("r", expanding=True)), {"r": list(REFS)})
        s.commit()
    finally:
        s.close()


@pytest.fixture(autouse=True)
def cleanup():
    _cleanup()
    yield
    _cleanup()


def _app(s, ref, decision, authority=COUNTY, when=date(2026, 3, 1)):
    a = DHLGHApplication(planning_authority=authority, source_entity="TEST", application_ref=ref,
                         development_description="of a synthetic test shed", site_address="Testtown, Co. Galway",
                         planning_status_current="DECIDED", decision=decision, application_type="PERMISSION",
                         date_received=date(2025, 12, 1), decision_date=when, source_system="dhlgh")
    s.add(a); s.flush()
    return a


def _doc(s, app, doc_id, status, items, kind):
    d = DecisionDocument(planning_authority=app.planning_authority, application_ref=app.application_ref,
                         dhlgh_application_id=app.id, council_doc_id=doc_id, doc_type="notification_of_decision",
                         source_url=f"https://example.invalid/{doc_id}", content_sha256="0" * 64, page_count=1,
                         extraction_method="pdftotext", raw_text="SYNTHETIC", parser_version="2", status=status,
                         stated_count=len(items), target_count=len(items), parsed_count=len(items))
    s.add(d); s.flush()
    for n, (text, reason) in enumerate(items, 1):
        s.add(DecisionItem(document_id=d.id, item_no=n, kind=kind, text=text, reason_text=reason))
    return d


def test_refused_application_returns_verbatim_reasons_with_source():
    s = SessionLocal()
    try:
        a = _app(s, REFS[0], "REFUSED")
        _doc(s, a, "800001", "validated", [("The quokkas habitat would be harmed.", None), ("Second synthetic reason.", None)], "refusal_reason")
        s.commit()
    finally:
        s.close()
    with engine.connect() as c:
        r = answer_question(c, f"Why was {REFS[0]} refused?")
    assert r["type"] == "application"
    assert [i["text"] for i in r["items"]] == ["The quokkas habitat would be harmed.", "Second synthetic reason."]
    assert r["source"]["source_url"] == "https://example.invalid/800001"
    assert "2 reasons for refusal" in r["message"]


def test_latest_validated_document_is_used_and_unvalidated_never_shown():
    s = SessionLocal()
    try:
        a = _app(s, REFS[1], "CONDITIONAL")
        _doc(s, a, "800010", "validated", [("Old condition.", "Old reason.")], "condition")
        _doc(s, a, "800011", "validated", [("New condition.", "In the interest of clarity.")], "condition")
        _doc(s, a, "800012", "count_mismatch", [("Unchecked condition.", None)], "condition")
        s.commit()
    finally:
        s.close()
    with engine.connect() as c:
        r = answer_question(c, f"conditions for {REFS[1]}")
    assert [i["text"] for i in r["items"]] == ["New condition."]
    assert r["items"][0]["reason_text"] == "In the interest of clarity."


def test_no_validated_document_says_not_in_records():
    s = SessionLocal()
    try:
        a = _app(s, REFS[2], "REFUSED")
        _doc(s, a, "800020", "count_mismatch", [("Unchecked reason.", None)], "refusal_reason")
        s.commit()
    finally:
        s.close()
    with engine.connect() as c:
        r = answer_question(c, f"why was {REFS[2]} refused")
    assert r["items"] == []
    assert NOT_IN_RECORDS in r["message"]
    assert "count" in r["note"]
    assert "Unchecked" not in str(r)


def test_same_ref_in_city_and_county_asks_which():
    s = SessionLocal()
    try:
        _app(s, REFS[3], "REFUSED", COUNTY)
        _app(s, REFS[3], "CONDITIONAL", CITY)
        s.commit()
    finally:
        s.close()
    with engine.connect() as c:
        r = answer_question(c, f"application {REFS[3]}")
        assert r["type"] == "clarify"
        r2 = answer_question(c, f"City application {REFS[3]}")
        assert r2["type"] == "application" and r2["application"]["planning_authority"] == CITY


def test_topic_search_finds_synthetic_reason():
    s = SessionLocal()
    try:
        a = _app(s, REFS[0], "REFUSED")
        _doc(s, a, "800030", "validated", [("The quokkas habitat would be harmed.", None)], "refusal_reason")
        s.commit()
    finally:
        s.close()
    with engine.connect() as c:
        r = answer_question(c, "refusals about quokkas")
    assert r["type"] == "search" and r["total"] == 1
    assert r["results"][0]["application_ref"] == REFS[0]
    assert "<<quokkas>>" in r["results"][0]["snippet"]


def test_unknown_reference_and_unknown_place():
    with engine.connect() as c:
        assert answer_question(c, "why was 99999909 refused")["type"] == "not_found"
        assert answer_question(c, "refusals in Zzyzxville")["type"] == "not_found"
