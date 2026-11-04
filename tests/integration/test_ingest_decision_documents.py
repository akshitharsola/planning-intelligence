from datetime import date
from pathlib import Path
import subprocess
import pytest
import sqlalchemy as sa

from src.core.db.session import SessionLocal
from src.core.models.decision_document import DecisionDocument
from src.core.models.decision_item import DecisionItem
from src.core.models.dhlgh_application import DHLGHApplication
from src.pipelines.decision_documents import IngestResult, ingest_application, ingest_authority
from src.sources.galway.decision_documents import DocLink

SPIKE_PDFS_DIR = Path(
    "/private/tmp/claude-501/-Users-akshitharsola-Documents-AiAgentic/6df0c992-c82b-4cdc-b4d0-d1ca911e909c/scratchpad/poc/pdfs_county"
)


def _cleanup():
    session = SessionLocal()
    try:
        session.execute(
            sa.text("DELETE FROM decision_documents WHERE application_ref LIKE 'INGEST_TEST/%'")
        )
        session.execute(
            sa.text("DELETE FROM dhlgh_applications WHERE application_ref LIKE 'INGEST_TEST/%'")
        )
        session.commit()
    finally:
        session.close()


@pytest.fixture(autouse=True)
def cleanup_after_test():
    _cleanup()
    yield
    _cleanup()


def read_spike_pdf(name: str) -> bytes:
    path = SPIKE_PDFS_DIR / f"{name}.pdf"
    if path.exists():
        return path.read_bytes()
    # Minimal fallback dummy PDF if spike dir is unavailable
    return b"%PDF-1.4\n1 0 obj<<>>endobj\nxref\n0 1\n0000000000 65535 f \ntrailer<<>>startxref\n9\n%%EOF"


class FakeCountyDocFetcher:
    def __init__(self, responses: dict[str, list[tuple[DocLink, bytes]]], eplan_counts: dict[str, int] | None = None):
        self.responses = responses
        self.eplan_counts = eplan_counts or {}
        self.pdf_fetch_counts: dict[str, int] = {}

    def fetch_list(self, ref: str) -> str:
        if ref not in self.responses:
            return ""
        links = self.responses[ref]
        html_rows = "".join(
            f'<tr><td><a href="ViewPDF.aspx?RefNo={ref}&amp;ViewFind=true&amp;ref={link.council_doc_id}">{link.council_doc_id} {link.doc_type}</a></td></tr>'
            for link, _ in links
        )
        return f"<table>{html_rows}</table>"

    def fetch_pdf(self, link: DocLink) -> bytes | None:
        self.pdf_fetch_counts[link.council_doc_id] = self.pdf_fetch_counts.get(link.council_doc_id, 0) + 1
        for links in self.responses.values():
            for doc_link, pdf_bytes in links:
                if doc_link.council_doc_id == link.council_doc_id:
                    return pdf_bytes
        return None

    def fetch_eplanning_condition_count(self, ref: str) -> int | None:
        return self.eplan_counts.get(ref)


def _seed_app(session, authority: str, ref: str, decision: str = "CONDITIONAL", decision_date: date = date(2024, 1, 1)) -> DHLGHApplication:
    app = DHLGHApplication(
        planning_authority=authority,
        source_entity="TEST",
        application_ref=ref,
        development_description="Test development",
        planning_status_current="DECIDED",
        decision=decision,
        date_received=date(2023, 11, 1),
        decision_date=decision_date,
        source_system="dhlgh",
    )
    session.add(app)
    session.commit()
    return app


def test_validated_notice_stores_document_and_items():
    session = SessionLocal()
    try:
        app = _seed_app(session, "Galway County Council", "INGEST_TEST/VAL", decision="REFUSED")
        pdf_bytes = read_spike_pdf("2360654_2469775")
        link = DocLink(
            council_doc_id="DOC_VAL_1",
            doc_type="notification_of_decision",
            url="https://apps.galwaycoco.ie/ViewExternalDocuments/ViewPDF.aspx?RefNo=INGEST_TESTVAL&ViewFind=true&ref=DOC_VAL_1",
        )
        fetcher = FakeCountyDocFetcher({"INGEST_TEST/VAL": [(link, pdf_bytes)]})

        res = ingest_application(session, fetcher, app)
        assert res.documents_stored == 1
        assert res.documents_skipped_unchanged == 0
        assert res.statuses["validated"] == 1

        doc = session.query(DecisionDocument).filter_by(council_doc_id="DOC_VAL_1").one()
        assert doc.status == "validated"
        assert doc.application_ref == "INGEST_TEST/VAL"
        assert doc.planning_authority == "Galway County Council"
        assert len(doc.items) == 4
        assert all(it.kind == "refusal_reason" for it in doc.items)
    finally:
        session.close()


def test_count_mismatch_stored_with_status_and_items():
    session = SessionLocal()
    try:
        app = _seed_app(session, "Galway County Council", "INGEST_TEST/MISMATCH", decision="CONDITIONAL")
        pdf_bytes = read_spike_pdf("2561329_2665281")
        link = DocLink(
            council_doc_id="DOC_MIS_1",
            doc_type="notification_of_decision",
            url="https://apps.galwaycoco.ie/ViewExternalDocuments/ViewPDF.aspx?RefNo=INGEST_TESTMISMATCH&ViewFind=true&ref=DOC_MIS_1",
        )
        fetcher = FakeCountyDocFetcher({"INGEST_TEST/MISMATCH": [(link, pdf_bytes)]})

        res = ingest_application(session, fetcher, app)
        assert res.documents_stored == 1
        assert res.statuses["count_mismatch"] == 1

        doc = session.query(DecisionDocument).filter_by(council_doc_id="DOC_MIS_1").one()
        assert doc.status == "count_mismatch"
        assert len(doc.items) == 13  # items are stored so audits can inspect them
    finally:
        session.close()


def test_scan_stored_as_needs_ocr_without_items():
    session = SessionLocal()
    try:
        app = _seed_app(session, "Galway County Council", "INGEST_TEST/SCAN", decision="CONDITIONAL")
        # Fake scanned PDF that produces fewer than 5 non-blank text lines
        pdf_bytes = b"%PDF-1.4\n1 0 obj<<>>endobj\nxref\n0 1\n0000000000 65535 f \ntrailer<<>>startxref\n9\n%%EOF"
        link = DocLink(
            council_doc_id="DOC_SCAN_1",
            doc_type="notification_of_decision",
            url="https://apps.galwaycoco.ie/ViewExternalDocuments/ViewPDF.aspx?RefNo=INGEST_TESTSCAN&ViewFind=true&ref=DOC_SCAN_1",
        )
        fetcher = FakeCountyDocFetcher({"INGEST_TEST/SCAN": [(link, pdf_bytes)]})

        res = ingest_application(session, fetcher, app)
        assert res.documents_stored == 1
        assert res.statuses["needs_ocr"] == 1

        doc = session.query(DecisionDocument).filter_by(council_doc_id="DOC_SCAN_1").one()
        assert doc.status == "needs_ocr"
        assert len(doc.items) == 0
    finally:
        session.close()


def test_rerun_unchanged_creates_no_duplicates():
    session = SessionLocal()
    try:
        app = _seed_app(session, "Galway County Council", "INGEST_TEST/RERUN", decision="REFUSED")
        pdf_bytes = read_spike_pdf("2360654_2469775")
        link = DocLink(
            council_doc_id="DOC_RERUN_1",
            doc_type="notification_of_decision",
            url="https://apps.galwaycoco.ie/ViewExternalDocuments/ViewPDF.aspx?RefNo=INGEST_TESTRERUN&ViewFind=true&ref=DOC_RERUN_1",
        )
        fetcher = FakeCountyDocFetcher({"INGEST_TEST/RERUN": [(link, pdf_bytes)]})

        res1 = ingest_application(session, fetcher, app)
        assert res1.documents_stored == 1
        assert res1.documents_skipped_unchanged == 0

        # Second run: identical sha256 -> skipped unchanged
        res2 = ingest_application(session, fetcher, app)
        assert res2.documents_stored == 0
        assert res2.documents_skipped_unchanged == 1

        docs = session.query(DecisionDocument).filter_by(council_doc_id="DOC_RERUN_1").all()
        assert len(docs) == 1
    finally:
        session.close()


def test_changed_hash_updates_row_and_replaces_items():
    session = SessionLocal()
    try:
        app = _seed_app(session, "Galway County Council", "INGEST_TEST/UPDATE", decision="CONDITIONAL")
        pdf1 = read_spike_pdf("2561413_2669234")  # 9 conditions
        link = DocLink(
            council_doc_id="DOC_UPD_1",
            doc_type="notification_of_decision",
            url="https://apps.galwaycoco.ie/ViewExternalDocuments/ViewPDF.aspx?RefNo=INGEST_TESTUPDATE&ViewFind=true&ref=DOC_UPD_1",
        )
        fetcher1 = FakeCountyDocFetcher({"INGEST_TEST/UPDATE": [(link, pdf1)]})
        ingest_application(session, fetcher1, app)

        doc = session.query(DecisionDocument).filter_by(council_doc_id="DOC_UPD_1").one()
        assert len(doc.items) == 9

        # Now council replaces the PDF with a new notice (e.g. 17 conditions from 2260277)
        pdf2 = read_spike_pdf("2260277_2378606")
        fetcher2 = FakeCountyDocFetcher({"INGEST_TEST/UPDATE": [(link, pdf2)]})
        res2 = ingest_application(session, fetcher2, app)
        assert res2.documents_stored == 1
        assert res2.documents_skipped_unchanged == 0

        session.expire_all()
        doc_updated = session.query(DecisionDocument).filter_by(council_doc_id="DOC_UPD_1").one()
        assert len(doc_updated.items) == 17
    finally:
        session.close()


def test_same_ref_other_authority_not_touched():
    session = SessionLocal()
    try:
        # Seed both County and City applications with the same ref
        county_app = _seed_app(session, "Galway County Council", "INGEST_TEST/SHARED_REF")
        city_app = _seed_app(session, "Galway City Council", "INGEST_TEST/SHARED_REF")

        pdf_bytes = read_spike_pdf("2360654_2469775")
        link = DocLink(
            council_doc_id="DOC_CO_1",
            doc_type="notification_of_decision",
            url="https://apps.galwaycoco.ie/ViewExternalDocuments/ViewPDF.aspx?RefNo=INGEST_TESTSHARED_REF&ViewFind=true&ref=DOC_CO_1",
        )
        fetcher = FakeCountyDocFetcher({"INGEST_TEST/SHARED_REF": [(link, pdf_bytes)]})

        ingest_application(session, fetcher, county_app)

        county_docs = (
            session.query(DecisionDocument)
            .filter_by(planning_authority="Galway County Council", application_ref="INGEST_TEST/SHARED_REF")
            .all()
        )
        city_docs = (
            session.query(DecisionDocument)
            .filter_by(planning_authority="Galway City Council", application_ref="INGEST_TEST/SHARED_REF")
            .all()
        )
        assert len(county_docs) == 1
        assert len(city_docs) == 0
    finally:
        session.close()


def test_dry_run_writes_nothing():
    session = SessionLocal()
    try:
        app = _seed_app(session, "Galway County Council", "INGEST_TEST/DRY_RUN", decision="REFUSED")
        pdf_bytes = read_spike_pdf("2360654_2469775")
        link = DocLink(
            council_doc_id="DOC_DRY_1",
            doc_type="notification_of_decision",
            url="https://apps.galwaycoco.ie/ViewExternalDocuments/ViewPDF.aspx?RefNo=INGEST_TESTDRY_RUN&ViewFind=true&ref=DOC_DRY_1",
        )
        fetcher = FakeCountyDocFetcher({"INGEST_TEST/DRY_RUN": [(link, pdf_bytes)]})

        res = ingest_application(session, fetcher, app, dry_run=True)
        assert res.statuses["validated"] == 1

        docs = session.query(DecisionDocument).filter_by(council_doc_id="DOC_DRY_1").all()
        assert len(docs) == 0
    finally:
        session.close()


def test_fetch_failure_does_not_abort_run():
    session = SessionLocal()
    try:
        app1 = _seed_app(session, "Galway County Council", "INGEST_TEST/ERR_1")
        app2 = _seed_app(session, "Galway County Council", "INGEST_TEST/ERR_2")

        pdf_bytes = read_spike_pdf("2360654_2469775")
        link2 = DocLink(
            council_doc_id="DOC_ERR_OK",
            doc_type="notification_of_decision",
            url="https://apps.galwaycoco.ie/ViewExternalDocuments/ViewPDF.aspx?RefNo=INGEST_TESTERR_2&ViewFind=true&ref=DOC_ERR_OK",
        )

        class ErrorThrowingFetcher(FakeCountyDocFetcher):
            def fetch_list(self, ref: str) -> str:
                if ref == "INGEST_TEST/ERR_1":
                    raise ConnectionResetError("Simulated connection reset")
                return super().fetch_list(ref)

        fetcher = ErrorThrowingFetcher({"INGEST_TEST/ERR_2": [(link2, pdf_bytes)]})

        # Run authority batch containing both apps
        summary = ingest_authority(
            session=session,
            fetcher=fetcher,
            authority="Galway County Council",
            refs=["INGEST_TEST/ERR_1", "INGEST_TEST/ERR_2"],
        )
        assert summary.documents_stored == 1
        assert summary.failures >= 1

        doc = session.query(DecisionDocument).filter_by(council_doc_id="DOC_ERR_OK").one()
        assert doc.status == "validated"
    finally:
        session.close()


def test_sampling_reproducible_and_multi_year():
    session = SessionLocal()
    try:
        # Seed 10 applications spanning years 2023, 2024, 2025
        seeded_apps = []
        for i in range(1, 11):
            yr = 2023 + (i % 3)
            app = _seed_app(
                session,
                "Galway County Council",
                f"INGEST_TEST/SAMPLE_{i:02d}",
                decision="CONDITIONAL",
                decision_date=date(yr, 6, 1),
            )
            seeded_apps.append(app)

        fetcher = FakeCountyDocFetcher({})

        # Capture apps processed via hook or spy
        processed_refs_run1 = []
        processed_refs_run2 = []
        processed_refs_diff_seed = []

        seeded_refs = [a.application_ref for a in seeded_apps]

        # Run 1 with seed=42
        class SpyFetcher(FakeCountyDocFetcher):
            def __init__(self, target_list):
                super().__init__({})
                self.target_list = target_list

            def fetch_list(self, ref: str) -> str:
                self.target_list.append(ref)
                return ""

        ingest_authority(
            session=session,
            fetcher=SpyFetcher(processed_refs_run1),
            authority="Galway County Council",
            refs=seeded_refs,
            sample=5,
            seed=42,
            dry_run=True,
        )

        # Run 2 with same seed=42
        ingest_authority(
            session=session,
            fetcher=SpyFetcher(processed_refs_run2),
            authority="Galway County Council",
            refs=seeded_refs,
            sample=5,
            seed=42,
            dry_run=True,
        )

        assert len(processed_refs_run1) == 5
        # Same seed -> exact same refs
        assert processed_refs_run1 == processed_refs_run2

        # Check that sampled apps span more than one decision year
        app_by_ref = {a.application_ref: a for a in seeded_apps}
        sampled_years = {app_by_ref[ref].decision_date.year for ref in processed_refs_run1}
        assert len(sampled_years) > 1

        # Run with different seed=99 produces different sample
        ingest_authority(
            session=session,
            fetcher=SpyFetcher(processed_refs_diff_seed),
            authority="Galway County Council",
            refs=seeded_refs,
            sample=5,
            seed=99,
            dry_run=True,
        )
        assert processed_refs_diff_seed != processed_refs_run1
    finally:
        session.close()

