import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.cleanup_stale_raw_files import cleanup_stale_raw_files


def _make_file(path: Path, age_days: float):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"%PDF-fake")
    old_time = time.time() - (age_days * 86400)
    os.utime(path, (old_time, old_time))


def test_deletes_ingested_file_older_than_30_days(tmp_path):
    stale = tmp_path / "2026" / "March" / "1-7" / "old.pdf"
    _make_file(stale, age_days=31)

    with patch("scripts.cleanup_stale_raw_files.is_file_ingested", return_value=True):
        result = cleanup_stale_raw_files(raw_dir=tmp_path, region="galway_city", max_age_days=30)

    assert "old.pdf" in result["deleted"]
    assert not stale.exists()


def test_does_not_delete_file_younger_than_30_days(tmp_path):
    fresh = tmp_path / "2026" / "March" / "1-7" / "fresh.pdf"
    _make_file(fresh, age_days=10)

    with patch("scripts.cleanup_stale_raw_files.is_file_ingested", return_value=True):
        result = cleanup_stale_raw_files(raw_dir=tmp_path, region="galway_city", max_age_days=30)

    assert "fresh.pdf" in result["skipped_too_new"]
    assert fresh.exists()


def test_does_not_delete_stale_file_that_was_never_ingested(tmp_path):
    stale_unfinished = tmp_path / "2026" / "March" / "1-7" / "unfinished.pdf"
    _make_file(stale_unfinished, age_days=45)

    with patch("scripts.cleanup_stale_raw_files.is_file_ingested", return_value=False):
        result = cleanup_stale_raw_files(raw_dir=tmp_path, region="galway_city", max_age_days=30)

    assert "unfinished.pdf" in result["skipped_not_ingested"]
    assert stale_unfinished.exists()


def test_dry_run_does_not_delete(tmp_path):
    stale = tmp_path / "2026" / "March" / "1-7" / "old.pdf"
    _make_file(stale, age_days=31)

    with patch("scripts.cleanup_stale_raw_files.is_file_ingested", return_value=True):
        result = cleanup_stale_raw_files(raw_dir=tmp_path, region="galway_city", max_age_days=30, dry_run=True)

    assert "old.pdf" in result["deleted"]
    assert stale.exists()


def test_prunes_empty_directories_after_deleting_last_file(tmp_path):
    stale = tmp_path / "2026" / "March" / "1-7" / "old.pdf"
    _make_file(stale, age_days=31)

    with patch("scripts.cleanup_stale_raw_files.is_file_ingested", return_value=True):
        cleanup_stale_raw_files(raw_dir=tmp_path, region="galway_city", max_age_days=30)

    assert not (tmp_path / "2026" / "March" / "1-7").exists()
    assert not (tmp_path / "2026" / "March").exists()
    assert not (tmp_path / "2026").exists()
    assert tmp_path.exists()


def test_missing_raw_dir_returns_empty_result(tmp_path):
    missing = tmp_path / "does_not_exist"
    result = cleanup_stale_raw_files(raw_dir=missing, region="galway_city", max_age_days=30)
    assert result == {"deleted": [], "skipped_not_ingested": [], "skipped_too_new": []}
