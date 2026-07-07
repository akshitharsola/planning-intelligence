# Weekly Scheduled Ingestion + City PDF Staging & Retention — Design

## Purpose

Today both ingestion CLIs (`scripts/ingest_galway_county.py`, `scripts/ingest_galway_city.py`) must be run manually. There is also no durable copy of the raw PDFs City ingestion downloads — they land in `/tmp/galway_city_ingest`, which is OS-managed scratch space wiped on reboot. This design adds:

1. A weekly, unattended local run of both ingestion CLIs (macOS launchd).
2. A persistent staging location for City's raw PDFs, so they survive across runs and reboots and can be inspected or reprocessed if a parsing bug is found.
3. Automatic cleanup of staged PDFs older than 30 days, but only once a file is confirmed ingested — never deleting a file that failed to fully ingest.

County ingestion is unaffected: it already reads directly from the live ArcGIS API with a persisted `OBJECTID` watermark (`ingestion_state` table) and produces no raw file artifact worth staging.

## Architecture

```
launchd (weekly, Sunday evening)
  -> scripts/run_weekly_ingestion.sh
       -> scripts/ingest_galway_county.py     (unchanged; API -> DB direct)
       -> scripts/ingest_galway_city.py       (PDFs now saved to data/galway/city/raw/, not /tmp)
       -> scripts/cleanup_stale_raw_files.py  (new; deletes ingested files older than 30 days)
     all output appended to logs/ingestion/YYYY-MM-DD.log
```

### 1. City PDF staging

- `scripts/ingest_galway_city.py` currently constructs `GalwayCityScraper(region_config=region_config, temp_dir=Path("/tmp/galway_city_ingest"))`. Change `temp_dir` to `Path("data/galway/city/raw")`.
- `GalwayCityScraper._build_local_path` already lays files out by year/month/week under `temp_dir`; no change needed there — only the base path moves.
- No behavior change to parsing/normalization/resolve/publish. This is purely relocating where the already-downloaded PDF bytes live on disk.
- `data/galway/city/temp/` (the old scratch dir referenced in past sessions) is untouched by this change and remains empty/unused, per existing pipeline design.

### 2. Retention & cleanup

- New script: `scripts/cleanup_stale_raw_files.py`.
- Walks `data/galway/city/raw/` recursively. For each PDF file:
  - Compute age from file mtime.
  - Look up `is_file_ingested(session, "galway_city", filename)` (existing helper in `src/core/ingestion_state.py` — confirmed `file_id` stored there is the plain filename, matching `local_path.name`, so no new correlation logic is needed).
  - Delete the file only if **both** `age > 30 days` **and** `is_file_ingested(...)` is `True`.
  - A file that is stale but *not yet* marked ingested (partial failure, per the self-healing retry design already in `ingest_galway_city.py`) is left alone and logged as skipped, so operators can see it and the next weekly run's retry logic can still pick it up.
- After deleting files, walk bottom-up and remove any now-empty week/month/year directories.
- CLI supports a `--dry-run` flag (prints what would be deleted without deleting), consistent with the existing ingestion scripts' `--dry-run` convention.

### 3. Weekly launchd job

- New shell wrapper `scripts/run_weekly_ingestion.sh`:
  - Activates `.venv`.
  - Runs `ingest_galway_county.py`, then `ingest_galway_city.py`, then `cleanup_stale_raw_files.py`, in that order.
  - Appends combined stdout/stderr to `logs/ingestion/$(date +%F).log` (new `logs/ingestion/` directory, gitignored).
  - Exits non-zero if any step fails, so launchd/log output makes failures visible; does not attempt automatic retry (both ingestion CLIs are already safely re-runnable on the next scheduled trigger or manually).
- New `com.planning-intelligence.weekly-ingestion.plist` (documented in a README section, not committed with machine-specific absolute paths baked in — the design doc will show a template and installation instructions, since launchd plists require the absolute path to the repo and to the venv Python, which are machine-specific).
- Scheduled for Sunday 20:00 local time via `StartCalendarInterval` (`Weekday: 0, Hour: 20, Minute: 0`).
- Documented manual verification steps: `launchctl load`, `launchctl start com.planning-intelligence.weekly-ingestion` to trigger immediately, `log show --predicate 'process == "launchd"' --last 1h` or checking `logs/ingestion/` to confirm a run happened.

## Error handling

- Both ingestion CLIs already handle per-record/per-file failures internally (failed county records are logged and skipped without blocking the watermark advance for successes; failed city PDFs are not marked ingested, enabling retry). This design does not change that behavior.
- `cleanup_stale_raw_files.py` only ever deletes confirmed-ingested + stale files — the worst case of a bug here is *slower* cleanup (files pile up), never data loss of not-yet-ingested data.
- If `run_weekly_ingestion.sh` fails partway (e.g. county ingestion errors), the script still attempts city ingestion and cleanup as independent steps (not short-circuited), since they are independent regions — a county failure shouldn't block a city run in the same week.

## Testing

- Unit tests for `cleanup_stale_raw_files.py`: age-cutoff boundary (29 vs 31 days), "skip if not ingested" behavior, empty-directory pruning — using a temp directory fixture and a mocked/real test DB session consistent with existing test patterns in `tests/`.
- No automated test for the `.plist`/launchd wiring itself (not meaningfully unit-testable); verified manually per the steps above.
- Existing 73 tests must continue to pass unchanged, since `GalwayCityScraper`'s internal path-building logic is untouched — only the `temp_dir` value passed in from the CLI changes.

## Out of scope

- No staging/retention added for County (confirmed: API-direct, no raw file artifact).
- No change to the chat/dashboard features from prior sessions.
- No cloud/hosting changes — this remains a fully local, launchd-based scheduled job per the project's current local-only design stance.
