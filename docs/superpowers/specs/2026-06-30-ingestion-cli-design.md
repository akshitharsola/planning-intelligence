# Ingestion CLI Design — Galway City & County

Date: 2026-06-30

## 1. Purpose

Neither Galway region has a runnable end-to-end ingestion entrypoint today —
only unit tests and (now-deleted) ad-hoc smoke-test scripts exist. This
design adds two standalone CLI scripts that wire the existing pipeline
stages (`discover → acquire → parse/normalize → resolve_and_upsert →
publish`) into something that can be run manually or via cron, plus the
persistence needed for incremental, idempotent re-runs.

Out of scope: actually scheduling the scripts (cron/CI) — that's a
follow-up decision once the scripts exist and have been run for real.

## 2. New persistence

One Alembic migration (`0002_create_ingestion_state.py`, following the
`<revision>_<verb>_<subject>.py` convention from the foundation design,
chained via `down_revision = '0001'`):

```sql
CREATE TABLE ingestion_state (
    region TEXT PRIMARY KEY,
    watermark TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE ingested_files (
    region TEXT NOT NULL,
    file_id TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (region, file_id)
);
```

`ingestion_state` holds County's `OBJECTID` watermark (as text, parsed to
int by the caller). `ingested_files` holds City's per-PDF dedup record,
keyed by the file identifier `discover()` already returns.

A thin module `src/core/ingestion_state.py` wraps both tables behind four
functions, used by both scripts — no pipeline stage needs to know about
SQL directly:

- `get_watermark(session, region: str) -> str | None`
- `set_watermark(session, region: str, watermark: str) -> None`
- `is_file_ingested(session, region: str, file_id: str) -> bool`
- `mark_file_ingested(session, region: str, file_id: str) -> None`

## 3. County script — `scripts/ingest_galway_county.py`

1. Open `SessionLocal()`. `get_watermark(session, "galway_county")` — `None`
   on first run (fetch all).
2. `GalwayCountyScraper.discover()` gains an optional `min_watermark: str |
   None` param. When set, the ArcGIS query adds a `OBJECTID > {min_watermark}`
   filter so only new records are paginated. `acquire()` is unchanged
   (passthrough).
3. For each returned record, in a try/except:
   - `normalize_county_row` → `resolve_and_upsert`
   - On success, track this record's `OBJECTID` as a candidate new watermark
     (running max over successes only)
   - On exception: log (region, OBJECTID, exception) at error level via
     `logging`, continue to the next record — do not abort the run
4. `publish(session, "galway_county", rows_ingested, parse_errors)`
5. If at least one record succeeded, `set_watermark` to the max successful
   `OBJECTID`. A record that failed never advances the watermark past it,
   so it's retried next run.
6. `--dry-run`: runs steps 1-3 (logging what *would* be written and the
   would-be new watermark) but skips `resolve_and_upsert`'s commit,
   `publish`, and `set_watermark`. Prints a summary: records discovered,
   would-succeed count, would-fail count, sample of up to 5 normalized rows.

## 4. City script — `scripts/ingest_galway_city.py`

1. Open `SessionLocal()`.
2. `GalwayCityScraper.discover()` → list of weekly PDF descriptors.
3. Filter out any whose `file_id` is already in `ingested_files` for
   `galway_city` (via `is_file_ingested`).
4. For each remaining file: `acquire()` it, then `extract_planning_table()`
   to get rows, then per-row try/except (`normalize_row` →
   `resolve_and_upsert`), logging and skipping failed rows same as County.
5. Once a file's rows have all been attempted (regardless of whether some
   rows failed), `mark_file_ingested` for that file — a file is never
   retried once attempted. A row that failed inside a successfully-attempted
   file is not retried; it's logged and dropped. (Decision: simplicity over
   self-healing — a transient row failure requires manual investigation via
   the error log, same as County's record-level failures would if they
   never resolve.)
6. `publish(session, "galway_city", rows_ingested, parse_errors)`.
7. `--dry-run`: same shape as County — discovers, filters already-ingested
   files, acquires and parses remaining files, prints a summary (files
   found, files skipped as already-ingested, rows parsed, sample rows) but
   does not call `resolve_and_upsert`'s commit, `publish`, or
   `mark_file_ingested`.

This also directly surfaces the `lookback_months` gotcha from the previous
session (a narrow lookback silently discovering 0 files) without needing a
real DB write to notice it.

## 5. Error handling (both scripts)

Per-record/per-row failures are logged and skipped, never fatal to the run.
This matters because these scripts are meant to run unattended (cron,
eventually) — one malformed PDF row or ArcGIS record must not block all
other new data. Failures are logged with enough identifying detail
(region, source identifier, exception) to debug from logs alone.

## 6. Testing

- Unit tests for `src/core/ingestion_state.py`: get/set watermark
  round-trip, is/mark file-ingested round-trip, against a real test
  Postgres, consistent with how `resolve_and_upsert` is already tested.
- Integration test per script: full flow against test Postgres with a
  stubbed source (mock `discover`/`acquire` return values, real
  normalize/resolve/publish/state-write), asserting: watermark advances
  correctly past successes only; a forced failure on one record doesn't
  block others; a second run with the same stub input ingests nothing new
  (idempotency via watermark / file-tracking).
