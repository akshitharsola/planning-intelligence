# Weekly Scheduled Ingestion + City PDF Staging & Retention Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Galway City ingestion run automatically once a week via macOS launchd, with its downloaded PDFs staged persistently on disk (instead of OS `/tmp`) and auto-cleaned 30 days after they're confirmed ingested. County is explicitly out of scope for this plan — it stays manual for now and will get its own follow-up plan later.

**Architecture:** `scripts/ingest_galway_city.py` changes its `temp_dir` from `/tmp/galway_city_ingest` to the persistent `data/galway/city/raw/`. A new `scripts/cleanup_stale_raw_files.py` deletes files under that directory older than 30 days, but only if `is_file_ingested()` confirms they were fully processed. A new `scripts/run_weekly_ingestion.sh` wrapper runs city ingestion then cleanup, logging to `logs/ingestion/`, triggered weekly by a new launchd `.plist` (Sunday 20:00 local time).

**Tech Stack:** Python 3.11, pytest, SQLAlchemy (existing `SessionLocal`/`ingestion_state` helpers), macOS launchd, bash.

## Global Constraints

- City-only scope for this plan — do not touch `scripts/ingest_galway_county.py` or County config/tests.
- Retention window is exactly 30 days, based on file mtime.
- Cleanup must only delete a file if `is_file_ingested(session, "galway_city", filename)` returns `True`. Never delete a stale-but-not-yet-ingested file.
- `data/galway/city/temp/` (the pre-existing scratch dir) is untouched — this plan introduces a **new**, separate `data/galway/city/raw/` directory for staged PDFs. Do not conflate the two.
- Follow existing test conventions: DB-touching tests get a `_cleanup()` helper deleting rows by a `CLITESTCITY/%`-style marker prefix, called both before and after the test body (see `tests/integration/test_ingest_galway_city.py`).
- Use `.venv/bin/python` (not Anaconda) for running tests — this project's `.venv` has the full dependency set (FastAPI, psycopg2, etc.).
- After any code file changes, run `graphify update .` and commit `graphify-out/` alongside the code change, per this repo's `CLAUDE.md`.

---

### Task 1: Stage City PDFs to a persistent directory instead of `/tmp`

**Files:**
- Modify: `scripts/ingest_galway_city.py:50` (the `GalwayCityScraper(...)` construction)
- Modify: `.gitignore` (add ignore rule for the new raw directory's contents, keep the directory itself trackable)
- Create: `data/galway/city/raw/.gitkeep`
- Test: `tests/integration/test_ingest_galway_city.py` (extend existing file)

**Interfaces:**
- Consumes: `GalwayCityScraper.__init__(region_config, temp_dir)` (existing, unchanged signature) — `src/sources/galway/city/scraper.py`.
- Produces: PDFs are now written under `data/galway/city/raw/<year>/<month>/<week>/...` instead of `/tmp/galway_city_ingest/...`. No other task depends on new names here — this only changes a path constant.

- [ ] **Step 1: Write a failing test asserting the new temp_dir path is used**

Add to `tests/integration/test_ingest_galway_city.py`:

```python
def test_run_city_ingestion_uses_persistent_raw_dir():
    from scripts.ingest_galway_city import run_city_ingestion
    import scripts.ingest_galway_city as mod

    captured = {}

    class _CapturingScraper:
        def __init__(self, region_config, temp_dir):
            captured["temp_dir"] = temp_dir

        def discover(self):
            return []

        def acquire(self, items):
            return []

    with patch.object(mod, "GalwayCityScraper", _CapturingScraper):
        run_city_ingestion()

    assert captured["temp_dir"] == Path("data/galway/city/raw")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/integration/test_ingest_galway_city.py::test_run_city_ingestion_uses_persistent_raw_dir -v`
Expected: FAIL — `captured["temp_dir"] == Path("/tmp/galway_city_ingest")`, not `data/galway/city/raw`.

- [ ] **Step 3: Change the temp_dir constant in the ingestion script**

In `scripts/ingest_galway_city.py`, change:

```python
scraper = GalwayCityScraper(region_config=region_config, temp_dir=Path("/tmp/galway_city_ingest"))
```

to:

```python
scraper = GalwayCityScraper(region_config=region_config, temp_dir=Path("data/galway/city/raw"))
```

- [ ] **Step 4: Create the directory placeholder and update .gitignore**

Create `data/galway/city/raw/.gitkeep` (empty file).

In `.gitignore`, find the existing block:

```
data/*/*/temp/*
!data/*/*/temp/.gitkeep
```

Add directly below it:

```
data/*/*/raw/*
!data/*/*/raw/.gitkeep
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/integration/test_ingest_galway_city.py::test_run_city_ingestion_uses_persistent_raw_dir -v`
Expected: PASS

- [ ] **Step 6: Run the full existing test suite to confirm no regression**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: All tests pass (73 existing + 1 new = 74).

- [ ] **Step 7: Update graphify and commit**

```bash
graphify update .
git add scripts/ingest_galway_city.py .gitignore data/galway/city/raw/.gitkeep tests/integration/test_ingest_galway_city.py graphify-out/
git commit -m "feat: stage City PDFs to data/galway/city/raw instead of /tmp"
```

---

### Task 2: Retention cleanup script for staged City PDFs

**Files:**
- Create: `scripts/cleanup_stale_raw_files.py`
- Test: `tests/unit/scripts/test_cleanup_stale_raw_files.py` (new test directory/file)

**Interfaces:**
- Consumes: `is_file_ingested(session: Session, region: str, file_id: str) -> bool` from `src.core.ingestion_state` (existing, confirmed `file_id` is the plain filename e.g. `"planning applications received week1.pdf"`, matching `Path.name` on disk). `SessionLocal` from `src.core.db.session` (existing).
- Produces: `cleanup_stale_raw_files(raw_dir: Path, region: str = "galway_city", max_age_days: int = 30, dry_run: bool = False) -> dict` returning `{"deleted": [...], "skipped_not_ingested": [...], "skipped_too_new": [...]}` (lists of filenames). This return shape is consumed by Task 3's wrapper script only via exit code / stdout, not imported directly — no cross-task import dependency beyond the function name and signature above.

- [ ] **Step 1: Write failing tests for the cleanup logic**

Create `tests/unit/scripts/__init__.py` (empty, for test discovery) and `tests/unit/scripts/test_cleanup_stale_raw_files.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/unit/scripts/test_cleanup_stale_raw_files.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.cleanup_stale_raw_files'`.

- [ ] **Step 3: Implement the cleanup script**

Create `scripts/cleanup_stale_raw_files.py`:

```python
"""
Deletes staged Galway City PDFs from data/galway/city/raw/ once they are
older than max_age_days AND confirmed ingested via ingested_files. Never
deletes a stale file that failed to ingest, so the existing self-healing
retry in ingest_galway_city.py still has the file to retry against. See
docs/superpowers/specs/2026-07-08-weekly-scheduler-and-staging-design.md.
"""

import argparse
import logging
import time
from pathlib import Path

from src.core.db.session import SessionLocal
from src.core.ingestion_state import is_file_ingested

logger = logging.getLogger(__name__)

DEFAULT_RAW_DIR = Path("data/galway/city/raw")
DEFAULT_REGION = "galway_city"
DEFAULT_MAX_AGE_DAYS = 30


def cleanup_stale_raw_files(
    raw_dir: Path = DEFAULT_RAW_DIR,
    region: str = DEFAULT_REGION,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
    dry_run: bool = False,
) -> dict:
    result = {"deleted": [], "skipped_not_ingested": [], "skipped_too_new": []}

    if not raw_dir.exists():
        return result

    session = SessionLocal()
    try:
        now = time.time()
        cutoff_seconds = max_age_days * 86400

        for pdf_path in sorted(raw_dir.rglob("*.pdf")):
            age_seconds = now - pdf_path.stat().st_mtime
            if age_seconds < cutoff_seconds:
                result["skipped_too_new"].append(pdf_path.name)
                continue

            if not is_file_ingested(session, region, pdf_path.name):
                result["skipped_not_ingested"].append(pdf_path.name)
                continue

            result["deleted"].append(pdf_path.name)
            if not dry_run:
                pdf_path.unlink()
    finally:
        session.close()

    if not dry_run:
        _prune_empty_dirs(raw_dir)

    return result


def _prune_empty_dirs(root: Path) -> None:
    for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean up stale, ingested City raw PDFs.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    result = cleanup_stale_raw_files(dry_run=args.dry_run)
    logger.info(
        "cleanup complete: deleted=%d skipped_not_ingested=%d skipped_too_new=%d",
        len(result["deleted"]),
        len(result["skipped_not_ingested"]),
        len(result["skipped_too_new"]),
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/scripts/test_cleanup_stale_raw_files.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Run the full test suite to confirm no regression**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: All tests pass.

- [ ] **Step 6: Update graphify and commit**

```bash
graphify update .
git add scripts/cleanup_stale_raw_files.py tests/unit/scripts/ graphify-out/
git commit -m "feat: add retention cleanup for stale, ingested City raw PDFs"
```

---

### Task 3: Weekly launchd job wiring both ingestion and cleanup

**Files:**
- Create: `scripts/run_weekly_ingestion.sh`
- Create: `com.planning-intelligence.weekly-ingestion.plist.template`
- Modify: `.gitignore` (ignore `logs/`)
- Modify: `README.md` (add a "Weekly scheduled ingestion (macOS)" section)

**Interfaces:**
- Consumes: `scripts/ingest_galway_city.py` (run as `python -m scripts.ingest_galway_city`, existing CLI entrypoint — confirmed via `if __name__ == "__main__":` pattern already used by that script), `scripts/cleanup_stale_raw_files.py` (Task 2's `main()` entrypoint, run as `python -m scripts.cleanup_stale_raw_files`).
- Produces: `logs/ingestion/YYYY-MM-DD.log` files (not consumed by any other task — terminal output of this plan).

- [ ] **Step 1: Confirm the existing CLI entrypoint pattern before wiring the wrapper**

Run: `tail -20 scripts/ingest_galway_city.py`
Expected: a `if __name__ == "__main__":` block calling `run_city_ingestion()` (or an argparse-driven `main()`), confirming `python -m scripts.ingest_galway_city` is a valid way to invoke it standalone. If the file instead only exposes `run_city_ingestion()` with no `__main__` guard, add one before proceeding (mirroring the pattern in `scripts/cleanup_stale_raw_files.py` from Task 2), as its own commit, before continuing to Step 2.

- [ ] **Step 2: Write the wrapper shell script**

Create `scripts/run_weekly_ingestion.sh`:

```bash
#!/usr/bin/env bash
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

LOG_DIR="$REPO_ROOT/logs/ingestion"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(date +%F).log"

source "$REPO_ROOT/.venv/bin/activate"

{
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') weekly ingestion run starting ==="

  echo "--- City ingestion ---"
  python -m scripts.ingest_galway_city
  city_status=$?

  echo "--- Cleanup stale raw files ---"
  python -m scripts.cleanup_stale_raw_files
  cleanup_status=$?

  echo "=== $(date '+%Y-%m-%d %H:%M:%S') weekly ingestion run finished (city=$city_status cleanup=$cleanup_status) ==="
} >> "$LOG_FILE" 2>&1

if [ "$city_status" -ne 0 ] || [ "$cleanup_status" -ne 0 ]; then
  exit 1
fi
exit 0
```

Make it executable:

Run: `chmod +x scripts/run_weekly_ingestion.sh`

- [ ] **Step 3: Smoke-test the wrapper script manually**

Run: `./scripts/run_weekly_ingestion.sh`
Expected: exits 0 (or 1 if the live City source is unreachable — check `logs/ingestion/<today>.log` for the actual error either way). Confirm the log file was created and contains both the "City ingestion" and "Cleanup stale raw files" section headers.

- [ ] **Step 4: Create the launchd plist template**

Create `com.planning-intelligence.weekly-ingestion.plist.template`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.planning-intelligence.weekly-ingestion</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>__REPO_ROOT__/scripts/run_weekly_ingestion.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>0</integer>
        <key>Hour</key>
        <integer>20</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>__REPO_ROOT__/logs/ingestion/launchd-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>__REPO_ROOT__/logs/ingestion/launchd-stderr.log</string>
</dict>
</plist>
```

- [ ] **Step 5: Add logs/ to .gitignore**

In `.gitignore`, add:

```
logs/
```

- [ ] **Step 6: Document installation and verification steps in README.md**

Add a new section to `README.md` (near the existing chat/setup sections):

```markdown
## Weekly scheduled ingestion (macOS)

City ingestion + raw-PDF cleanup run automatically once a week via macOS
launchd (Sundays at 20:00 local time). County remains manual for now.

**Install:**

1. Copy the template and fill in your absolute repo path:
   ```bash
   sed "s|__REPO_ROOT__|$(pwd)|g" com.planning-intelligence.weekly-ingestion.plist.template \
     > ~/Library/LaunchAgents/com.planning-intelligence.weekly-ingestion.plist
   ```
2. Load it:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.planning-intelligence.weekly-ingestion.plist
   ```

**Verify without waiting a week:**

```bash
launchctl start com.planning-intelligence.weekly-ingestion
tail -f logs/ingestion/$(date +%F).log
```

**Uninstall:**

```bash
launchctl unload ~/Library/LaunchAgents/com.planning-intelligence.weekly-ingestion.plist
rm ~/Library/LaunchAgents/com.planning-intelligence.weekly-ingestion.plist
```
```

- [ ] **Step 7: Run the full test suite one final time**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: All tests pass (no test-affecting changes in this task, this is a final regression check before committing).

- [ ] **Step 8: Update graphify and commit**

```bash
graphify update .
git add scripts/run_weekly_ingestion.sh com.planning-intelligence.weekly-ingestion.plist.template .gitignore README.md graphify-out/
git commit -m "feat: add weekly launchd job for City ingestion and raw-file cleanup"
```

---

## Out of scope (deferred)

- County ingestion scheduling — will be scoped and planned separately once City is verified working end-to-end for a real week.
- Any raw-payload staging for County (per the approved design, County has no file artifact to stage).
