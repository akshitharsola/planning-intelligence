from unittest.mock import patch

from src.core.db.session import SessionLocal
from src.core.ingestion_state import get_watermark
from scripts.ingest_galway_county import run_county_ingestion

REGION = "galway_county"


def _cleanup():
    session = SessionLocal()
    try:
        session.execute(
            __import__("sqlalchemy").text(
                "DELETE FROM application_events WHERE application_ref LIKE 'CLITEST/%'"
            )
        )
        session.execute(
            __import__("sqlalchemy").text(
                "DELETE FROM applications WHERE application_ref LIKE 'CLITEST/%'"
            )
        )
        session.execute(
            __import__("sqlalchemy").text(
                "DELETE FROM ingestion_state WHERE region = :region"
            ),
            {"region": REGION},
        )
        session.commit()
    finally:
        session.close()


def _fake_records(ids):
    return [
        {
            "OBJECTID": i,
            "ApplicationNumber": f"CLITEST/{i:04d}",
            "ApplicantName": "Test Applicant",
            "Location": "Test Townland",
            "Description": "Test development",
            "ApplicationType": "Permission",
            "ReceivedDate": "01/03/2026",
            "DecisionDate": None,
            "DecisionDueDate": None,
            "Decision": "n\\a",
            "ApplicationStatus": "Application Open",
            "MoreInfo": None,
        }
        for i in ids
    ]


def test_first_run_ingests_all_and_sets_watermark():
    _cleanup()
    try:
        with patch(
            "src.sources.galway.county.scraper.GalwayCountyScraper.discover",
            return_value=_fake_records([1001, 1002, 1003]),
        ):
            result = run_county_ingestion()

        assert result["discovered"] == 3
        assert result["ingested"] == 3
        assert result["failed"] == 0
        assert result["new_watermark"] == "1003"

        session = SessionLocal()
        try:
            assert get_watermark(session, REGION) == "1003"
        finally:
            session.close()
    finally:
        _cleanup()


def test_second_run_with_stored_watermark_ingests_only_new():
    _cleanup()
    try:
        with patch(
            "src.sources.galway.county.scraper.GalwayCountyScraper.discover",
            return_value=_fake_records([2001, 2002]),
        ):
            run_county_ingestion()

        def discover_second(self):
            assert self.region_config.get("watermark") == 2002
            return _fake_records([2003])

        with patch(
            "src.sources.galway.county.scraper.GalwayCountyScraper.discover",
            discover_second,
        ):
            result = run_county_ingestion()

        assert result["discovered"] == 1
        assert result["ingested"] == 1
        assert result["new_watermark"] == "2003"
    finally:
        _cleanup()


def test_forced_failure_does_not_block_later_successes_from_advancing_watermark():
    """A mid-batch failure (OBJECTID 3002) must not block 3003 (a later,
    successful OBJECTID) from advancing the watermark. The failed record
    itself is simply not counted as a success — per the spec (section 2),
    a specific failed OBJECTID can still end up permanently un-retried if
    a later OBJECTID's success advances the watermark past it. That is a
    documented, accepted limitation, not something this test should treat
    as a bug."""
    _cleanup()
    try:
        records = _fake_records([3001, 3002, 3003])

        def discover_with_bad_row(self):
            return records

        # Force normalize_county_row to raise only for OBJECTID 3002 —
        # patched at the call site inside scripts.ingest_galway_county,
        # not at its definition module, so the script's own reference is
        # the one replaced.
        from src.core.normalization.galway_county import normalize_county_row as real_normalize

        def failing_normalize(raw_row, region_config, source_file):
            if raw_row.get("OBJECTID") == 3002:
                raise ValueError("forced failure for test")
            return real_normalize(raw_row, region_config, source_file)

        with patch(
            "src.sources.galway.county.scraper.GalwayCountyScraper.discover",
            discover_with_bad_row,
        ), patch(
            "scripts.ingest_galway_county.normalize_county_row",
            failing_normalize,
        ):
            result = run_county_ingestion()

        assert result["discovered"] == 3
        assert result["ingested"] == 2
        assert result["failed"] == 1
        # 3001 and 3003 succeeded; 3002 failed. Watermark is the max
        # successful OBJECTID (3003), per spec section 3 step 5 — it does
        # not get "stuck" behind 3002.
        assert result["new_watermark"] == "3003"

        session = SessionLocal()
        try:
            from sqlalchemy import text
            row = session.execute(
                text("SELECT 1 FROM applications WHERE application_ref = 'CLITEST/3002'")
            ).first()
            assert row is None, "the failed record must not have been written"
        finally:
            session.close()
    finally:
        _cleanup()


def test_dry_run_does_not_write_to_db_or_set_watermark():
    _cleanup()
    try:
        with patch(
            "src.sources.galway.county.scraper.GalwayCountyScraper.discover",
            return_value=_fake_records([4001]),
        ):
            result = run_county_ingestion(dry_run=True)

        assert result["discovered"] == 1
        assert result["ingested"] == 1  # "would ingest" count

        session = SessionLocal()
        try:
            assert get_watermark(session, REGION) is None
            from sqlalchemy import text
            row = session.execute(
                text("SELECT 1 FROM applications WHERE application_ref = 'CLITEST/4001'")
            ).first()
            assert row is None
        finally:
            session.close()
    finally:
        _cleanup()
