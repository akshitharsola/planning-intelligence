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


def read_spike_pdf(name: str, need_parse: bool = True) -> bytes:
    path = SPIKE_PDFS_DIR / f"{name}.pdf"
    if path.exists():
        return path.read_bytes()
    if not need_parse:
        # Any PDF bytes will do for tests that do not check parsed content.
        return DUMMY_PDF
    # The spike PDFs are real council notices and are never committed (public repo).
    # Without them these tests cannot check parsing, so skip instead of failing.
    pytest.skip(f"spike PDF {name}.pdf not available on this machine")


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
        pdf_bytes = read_spike_pdf("2360654_2469775", need_parse=False)
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

        pdf_bytes = read_spike_pdf("2360654_2469775", need_parse=False)
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



# --- Phase 3: --skip-known, --refresh, --until-year, progress logging ---

DUMMY_PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\nxref\n0 1\n0000000000 65535 f \ntrailer<<>>startxref\n9\n%%EOF"


def _link(ref: str, doc_id: str) -> DocLink:
    clean = ref.replace("/", "")
    return DocLink(
        council_doc_id=doc_id,
        doc_type="notification_of_decision",
        url=f"https://apps.galwaycoco.ie/ViewExternalDocuments/ViewPDF.aspx?RefNo={clean}&ViewFind=true&ref={doc_id}",
    )


class CountingFetcher(FakeCountyDocFetcher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_calls: list[str] = []

    def fetch_list(self, ref: str) -> str:
        self.list_calls.append(ref)
        return super().fetch_list(ref)


def test_skip_known_second_run_makes_zero_pdf_requests():
    session = SessionLocal()
    try:
        _seed_app(session, "Galway County Council", "INGEST_TEST/SKIP_1")
        _seed_app(session, "Galway County Council", "INGEST_TEST/SKIP_2")
        responses = {
            "INGEST_TEST/SKIP_1": [(_link("INGEST_TEST/SKIP_1", "DOC_SKIP_1"), DUMMY_PDF)],
            "INGEST_TEST/SKIP_2": [(_link("INGEST_TEST/SKIP_2", "DOC_SKIP_2"), DUMMY_PDF)],
        }
        refs = ["INGEST_TEST/SKIP_1", "INGEST_TEST/SKIP_2"]

        first = CountingFetcher(responses)
        res1 = ingest_authority(session=session, fetcher=first, refs=refs)
        assert res1.documents_stored == 2
        assert sum(first.pdf_fetch_counts.values()) == 2

        second = CountingFetcher(responses)
        res2 = ingest_authority(session=session, fetcher=second, refs=refs)
        assert sum(second.pdf_fetch_counts.values()) == 0
        assert sorted(second.list_calls) == refs  # list pages are still fetched
        assert res2.documents_stored == 0
        assert res2.documents_skipped_known == 2
        assert res2.statuses["needs_ocr"] == 2
        assert session.query(DecisionDocument).filter(
            DecisionDocument.application_ref.in_(refs)
        ).count() == 2
    finally:
        session.close()


def test_refresh_refetches_known_pdfs_and_checks_hash():
    session = SessionLocal()
    try:
        _seed_app(session, "Galway County Council", "INGEST_TEST/REFRESH")
        responses = {"INGEST_TEST/REFRESH": [(_link("INGEST_TEST/REFRESH", "DOC_REFRESH"), DUMMY_PDF)]}
        ingest_authority(session=session, fetcher=CountingFetcher(responses), refs=["INGEST_TEST/REFRESH"])

        again = CountingFetcher(responses)
        res = ingest_authority(
            session=session, fetcher=again, refs=["INGEST_TEST/REFRESH"], skip_known=False
        )
        assert again.pdf_fetch_counts == {"DOC_REFRESH": 1}
        assert res.documents_skipped_known == 0
        assert res.documents_skipped_unchanged == 1
    finally:
        session.close()


def test_skip_known_off_by_default_for_single_application():
    session = SessionLocal()
    try:
        app = _seed_app(session, "Galway County Council", "INGEST_TEST/SINGLE")
        responses = {"INGEST_TEST/SINGLE": [(_link("INGEST_TEST/SINGLE", "DOC_SINGLE"), DUMMY_PDF)]}
        ingest_application(session, CountingFetcher(responses), app)
        again = CountingFetcher(responses)
        res = ingest_application(session, again, app)
        assert again.pdf_fetch_counts == {"DOC_SINGLE": 1}
        assert res.documents_skipped_unchanged == 1
    finally:
        session.close()


def test_until_year_limits_selection_to_year_window():
    session = SessionLocal()
    try:
        for year in (2023, 2024, 2025, 2026):
            _seed_app(
                session,
                "Galway County Council",
                f"INGEST_TEST/YEAR_{year}",
                decision_date=date(year, 12, 31) if year == 2025 else date(year, 1, 1),
            )
        fetcher = CountingFetcher({})
        ingest_authority(
            session=session, fetcher=fetcher, since_year=2025, until_year=2025, dry_run=True
        )
        test_calls = [r for r in fetcher.list_calls if r.startswith("INGEST_TEST/YEAR_")]
        assert test_calls == ["INGEST_TEST/YEAR_2025"]
    finally:
        session.close()


def test_progress_logged_every_25_applications(caplog):
    session = SessionLocal()
    try:
        refs = []
        for i in range(30):
            ref = f"INGEST_TEST/PROG_{i:02d}"
            _seed_app(session, "Galway County Council", ref)
            refs.append(ref)
        with caplog.at_level("INFO", logger="src.pipelines.decision_documents"):
            ingest_authority(session=session, fetcher=CountingFetcher({}), refs=refs, dry_run=True)
        progress = [r.getMessage() for r in caplog.records if r.getMessage().startswith("Progress")]
        assert len(progress) == 2  # after app 25 and at the end (30)
        assert progress[0].startswith("Progress 25/30")
        assert progress[1].startswith("Progress 30/30")
    finally:
        session.close()


def test_keyboard_interrupt_keeps_committed_documents_and_resumes():
    session = SessionLocal()
    try:
        _seed_app(session, "Galway County Council", "INGEST_TEST/INT_1", decision_date=date(2024, 1, 1))
        _seed_app(session, "Galway County Council", "INGEST_TEST/INT_2", decision_date=date(2024, 1, 2))
        responses = {
            "INGEST_TEST/INT_1": [(_link("INGEST_TEST/INT_1", "DOC_INT_1"), DUMMY_PDF)],
            "INGEST_TEST/INT_2": [(_link("INGEST_TEST/INT_2", "DOC_INT_2"), DUMMY_PDF)],
        }
        refs = ["INGEST_TEST/INT_1", "INGEST_TEST/INT_2"]

        class InterruptingFetcher(CountingFetcher):
            def fetch_list(self, ref: str) -> str:
                if ref == "INGEST_TEST/INT_2":
                    raise KeyboardInterrupt
                return super().fetch_list(ref)

        with pytest.raises(KeyboardInterrupt):
            ingest_authority(session=session, fetcher=InterruptingFetcher(responses), refs=refs)
        assert session.query(DecisionDocument).filter_by(council_doc_id="DOC_INT_1").count() == 1

        resume = CountingFetcher(responses)
        res = ingest_authority(session=session, fetcher=resume, refs=refs)
        assert resume.pdf_fetch_counts == {"DOC_INT_2": 1}
        assert res.documents_stored == 1
        assert res.documents_skipped_known == 1
    finally:
        session.close()


def test_list_page_failure_is_counted_as_failure():
    from src.sources.galway.decision_documents import ListFetchError

    session = SessionLocal()
    try:
        app = _seed_app(session, "Galway County Council", "INGEST_TEST/LISTFAIL")

        class Failing(CountingFetcher):
            def fetch_list(self, ref: str) -> str:
                raise ListFetchError("timed out")

        res = ingest_application(session, Failing({}), app)
        assert res.failures == 1
        assert res.documents_stored == 0
    finally:
        session.close()


def test_run_stops_after_consecutive_application_failures():
    from src.sources.galway.decision_documents import ListFetchError

    session = SessionLocal()
    try:
        refs = []
        for i in range(6):
            ref = f"INGEST_TEST/STALL_{i}"
            _seed_app(session, "Galway County Council", ref, decision_date=date(2024, 1, 1 + i))
            refs.append(ref)

        class Failing(CountingFetcher):
            def fetch_list(self, ref: str) -> str:
                self.list_calls.append(ref)
                raise ListFetchError("timed out")

        fetcher = Failing({})
        with pytest.raises(RuntimeError, match="consecutive"):
            ingest_authority(session=session, fetcher=fetcher, refs=refs, max_consecutive_failures=3)
        assert len(fetcher.list_calls) == 3
    finally:
        session.close()


def test_success_resets_consecutive_failure_count():
    from src.sources.galway.decision_documents import ListFetchError

    session = SessionLocal()
    try:
        refs = []
        for i in range(6):
            ref = f"INGEST_TEST/FLAKY_{i}"
            _seed_app(session, "Galway County Council", ref, decision_date=date(2024, 1, 1 + i))
            refs.append(ref)

        class Flaky(CountingFetcher):
            def fetch_list(self, ref: str) -> str:
                self.list_calls.append(ref)
                if ref.endswith(("_2", "_5")):
                    return ""
                raise ListFetchError("timed out")

        fetcher = Flaky({})
        res = ingest_authority(session=session, fetcher=fetcher, refs=refs, max_consecutive_failures=3)
        assert len(fetcher.list_calls) == 6
        assert res.failures == 4
    finally:
        session.close()
