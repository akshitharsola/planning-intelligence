from unittest.mock import patch

import sqlalchemy as sa

from src.core.db.session import SessionLocal
from src.core.ingestion_state import get_watermark
from scripts.ingest_dhlgh import run_dhlgh_ingestion

REGION = "dhlgh_galway"


def _cleanup():
    session = SessionLocal()
    try:
        session.execute(
            sa.text("DELETE FROM dhlgh_applications WHERE application_ref LIKE 'CLITEST/%'")
        )
        session.execute(
            sa.text("DELETE FROM ingestion_state WHERE region = :region"),
            {"region": REGION},
        )
        session.commit()
    finally:
        session.close()


def _fake_records(ids):
    return [
        {
            "OBJECTID": i,
            "PlanningAuthority": "Galway City Council",
            "ApplicationNumber": f"CLITEST/{i:04d}",
            "DevelopmentDescription": "Test development",
            "DevelopmentAddress": "Test Address, Galway",
            "DevelopmentPostcode": "",
            "ApplicationStatus": "Received",
            "ApplicationType": "Permission",
            "ReceivedDate": "01/03/2026",
            "DecisionDate": None,
            "Decision": None,
        }
        for i in ids
    ]


def test_first_run_ingests_all_and_sets_watermark():
    _cleanup()
    try:
        with patch(
            "src.sources.dhlgh.scraper.DHLGHScraper.discover",
            return_value=_fake_records([1001, 1002, 1003]),
        ):
            result = run_dhlgh_ingestion()

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
            "src.sources.dhlgh.scraper.DHLGHScraper.discover",
            return_value=_fake_records([2001, 2002]),
        ):
            run_dhlgh_ingestion()

        def discover_second(self):
            assert self.region_config.get("watermark") == 2002
            return _fake_records([2003])

        with patch(
            "src.sources.dhlgh.scraper.DHLGHScraper.discover",
            discover_second,
        ):
            result = run_dhlgh_ingestion()

        assert result["discovered"] == 1
        assert result["ingested"] == 1
        assert result["new_watermark"] == "2003"
    finally:
        _cleanup()


def test_forced_failure_does_not_block_later_successes_from_advancing_watermark():
    _cleanup()
    try:
        records = _fake_records([3001, 3002, 3003])

        def discover_with_bad_row(self):
            return records

        from src.core.normalization.dhlgh import normalize_dhlgh_row as real_normalize

        def failing_normalize(raw_row, region_config, source_file):
            if raw_row.get("OBJECTID") == 3002:
                raise ValueError("forced failure for test")
            return real_normalize(raw_row, region_config, source_file)

        with patch(
            "src.sources.dhlgh.scraper.DHLGHScraper.discover",
            discover_with_bad_row,
        ), patch(
            "scripts.ingest_dhlgh.normalize_dhlgh_row",
            failing_normalize,
        ):
            result = run_dhlgh_ingestion()

        assert result["discovered"] == 3
        assert result["ingested"] == 2
        assert result["failed"] == 1
        assert result["new_watermark"] == "3003"

        session = SessionLocal()
        try:
            row = session.execute(
                sa.text("SELECT 1 FROM dhlgh_applications WHERE application_ref = 'CLITEST/3002'")
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
            "src.sources.dhlgh.scraper.DHLGHScraper.discover",
            return_value=_fake_records([4001]),
        ):
            result = run_dhlgh_ingestion(dry_run=True)

        assert result["discovered"] == 1
        assert result["ingested"] == 1

        session = SessionLocal()
        try:
            assert get_watermark(session, REGION) is None
            row = session.execute(
                sa.text("SELECT 1 FROM dhlgh_applications WHERE application_ref = 'CLITEST/4001'")
            ).first()
            assert row is None
        finally:
            session.close()
    finally:
        _cleanup()
