from pathlib import Path
from unittest.mock import patch

from src.core.db.session import SessionLocal
from src.core.ingestion_state import is_file_ingested
from scripts.ingest_galway_city import run_city_ingestion, _match_source_type

REGION = "galway_city"


def _cleanup():
    session = SessionLocal()
    try:
        session.execute(
            __import__("sqlalchemy").text(
                "DELETE FROM application_events WHERE application_ref LIKE 'CLITESTCITY/%'"
            )
        )
        session.execute(
            __import__("sqlalchemy").text(
                "DELETE FROM applications WHERE application_ref LIKE 'CLITESTCITY/%'"
            )
        )
        session.execute(
            __import__("sqlalchemy").text("DELETE FROM ingested_files WHERE region = :region"),
            {"region": REGION},
        )
        session.commit()
    finally:
        session.close()


def test_match_source_type_finds_pattern_key():
    # Substrings in config/galway/city.yaml's pdf_patterns are matched
    # against the lowercased filename literally (spaces, not underscores) —
    # mirrors GalwayCityScraper.discover()'s own matching at
    # src/sources/galway/city/scraper.py:67.
    assert _match_source_type("planning applications received week1.pdf") == "received"
    assert _match_source_type("planning applications granted week1.pdf") == "granted"
    assert _match_source_type("unmatched_file.pdf") is None


def test_first_run_ingests_all_rows_and_marks_file():
    _cleanup()
    try:
        fake_link = {"url": "https://example.test/x.pdf", "filename": "planning applications received week1.pdf",
                     "year": 2026, "month_num": 3, "month_name": "March", "week_range": "1-7"}
        fake_rows = [{
            "file_number": "CLITESTCITY/0001",
            "applicant": "Test Applicant",
            "app_type": "P",
            "date_received": "02/03/2026",
            "description": "Test development at Bohermore Galway",
        }]

        with patch(
            "src.sources.galway.city.scraper.GalwayCityScraper.discover",
            return_value=[fake_link],
        ), patch(
            "src.sources.galway.city.scraper.GalwayCityScraper.acquire",
            return_value=[Path("/tmp/planning applications received week1.pdf")],
        ), patch(
            "scripts.ingest_galway_city.extract_planning_table",
            return_value=fake_rows,
        ):
            result = run_city_ingestion()

        assert result["discovered"] == 1
        assert result["skipped_already_ingested"] == 0
        assert result["ingested"] == 1
        assert result["failed"] == 0

        session = SessionLocal()
        try:
            assert is_file_ingested(session, REGION, "planning applications received week1.pdf") is True
        finally:
            session.close()
    finally:
        _cleanup()


def test_second_run_skips_already_ingested_file():
    _cleanup()
    try:
        fake_link = {"url": "https://example.test/x.pdf", "filename": "planning applications received week1.pdf",
                     "year": 2026, "month_num": 3, "month_name": "March", "week_range": "1-7"}
        fake_rows = [{
            "file_number": "CLITESTCITY/0002",
            "applicant": "Test Applicant",
            "app_type": "P",
            "date_received": "02/03/2026",
            "description": "Test development at Bohermore Galway",
        }]

        with patch(
            "src.sources.galway.city.scraper.GalwayCityScraper.discover",
            return_value=[fake_link],
        ), patch(
            "src.sources.galway.city.scraper.GalwayCityScraper.acquire",
            return_value=[Path("/tmp/planning applications received week1.pdf")],
        ), patch(
            "scripts.ingest_galway_city.extract_planning_table",
            return_value=fake_rows,
        ):
            run_city_ingestion()
            result = run_city_ingestion()

        assert result["discovered"] == 1
        assert result["skipped_already_ingested"] == 1
        assert result["ingested"] == 0
    finally:
        _cleanup()


def test_file_with_one_bad_row_is_not_marked_ingested_and_retries():
    _cleanup()
    try:
        fake_link = {"url": "https://example.test/x.pdf", "filename": "planning applications received week1.pdf",
                     "year": 2026, "month_num": 3, "month_name": "March", "week_range": "1-7"}
        bad_rows = [{
            "file_number": "CLITESTCITY/0003",
            "applicant": "Test Applicant",
            "app_type": "P",
            "date_received": None,  # not enough alone to fail Pydantic since normalize_row
                                     # defaults date_received via datetime.now() if falsy --
                                     # use an applicant that's required-empty instead to force
                                     # a real failure: omit applicant_name's source key entirely
                                     # is still fine since normalize_row defaults to "". Force
                                     # failure via a non-string description type instead.
            "description": 12345,  # wrong type -> ApplicationCreate validation error
        }]
        good_rows = [{
            "file_number": "CLITESTCITY/0004",
            "applicant": "Test Applicant",
            "app_type": "P",
            "date_received": "02/03/2026",
            "description": "Test development at Bohermore Galway",
        }]

        with patch(
            "src.sources.galway.city.scraper.GalwayCityScraper.discover",
            return_value=[fake_link],
        ), patch(
            "src.sources.galway.city.scraper.GalwayCityScraper.acquire",
            return_value=[Path("/tmp/planning applications received week1.pdf")],
        ), patch(
            "scripts.ingest_galway_city.extract_planning_table",
            return_value=good_rows + bad_rows,
        ):
            result = run_city_ingestion()

        assert result["ingested"] == 1
        assert result["failed"] == 1

        session = SessionLocal()
        try:
            assert is_file_ingested(session, REGION, "planning applications received week1.pdf") is False
        finally:
            session.close()
    finally:
        _cleanup()
