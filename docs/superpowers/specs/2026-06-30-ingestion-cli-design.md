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

**Reuse, not parallel logic.** Both scripts are thin orchestration over the
pipeline functions already defined in the foundation design and built in
Tasks 1-10 — `load_region_config` (`src/pipelines/discover.py:6`),
`<Scraper>.discover()`/`.acquire()` (`src/sources/galway/{city,county}/`),
`extract_planning_table` (`src/parsers/pdf_lines/galway_city.py:49`),
`normalize_row`/`normalize_county_row` (`src/pipelines/normalize.py:23`,
`src/core/normalization/galway_county.py:26`), `resolve_and_upsert`
(`src/pipelines/resolve.py:15`), and `publish`
(`src/pipelines/publish.py:11`). The CLI scripts add **only** two things
that don't already exist: the per-record try/except loop (sequencing, not
new business logic) and the `ingestion_state` read/writes around it. No
pipeline stage is reimplemented or forked — `resolve_and_upsert`'s upsert
semantics, `publish`'s commit + metrics recording, and existing
normalization logic are called as-is, unmodified, exactly as County's
prior end-to-end smoke test already proved they work.

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

**Risk — unverified operational assumption, not a guaranteed source
contract.** This strategy depends on `OBJECTID` being a stable,
monotonically-increasing insertion order from the ArcGIS Feature Service —
i.e. a record's `OBJECTID` never changes once assigned, and new records are
always assigned higher values than all existing ones. Status of this
assumption:

- **What's actually been verified:** a single one-shot fetch (discover →
  normalize → write → re-read in a fresh session) against live data, last
  session. `OBJECTID` ordering looked consistent across that one sample.
- **What has NOT been verified:** repeated incremental runs — i.e. whether
  querying `OBJECTID > watermark` on a second run actually returns only
  and all the genuinely-new records, with no gaps, over time. That is
  exactly the behavior this CLI introduces and has not been exercised
  against the real source yet, only designed.
- Esri/ArcGIS does not document `OBJECTID` immutability or strict
  monotonicity as a guaranteed contract; Galway County Council has not
  documented it either — it is an observed pattern in one sample, not a
  promise.
- **Failure mode if the assumption breaks:** if the council ever reorders,
  reindexes, or backfills the underlying feature layer (e.g. importing
  older paper records with `OBJECTID`s assigned after newer ones), a "max
  successful OBJECTID" watermark would silently skip those backfilled
  records permanently — they'd have an `OBJECTID` below the stored
  watermark and never be queried again.
- Mitigation is out of scope for this design (it would need a secondary
  check, e.g. periodically re-querying near `OBJECTID` 0 or cross-checking
  total record counts against the source). This must stay flagged as a
  live risk — not treated as settled — until incremental runs have
  actually been observed over real time against the live source, which
  this design alone does not provide.

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
5. A file is marked ingested (`mark_file_ingested`) **only if every row in
   it succeeded** (zero row-level exceptions). If any row failed, the file
   is left unmarked, so the *entire file* — including its already-succeeded
   rows — is retried in full next run. This is deliberately self-healing
   rather than "mark done regardless": `resolve_and_upsert` is idempotent
   (upsert on natural key), so re-processing already-good rows on retry is
   cheap, and a transient downstream failure (e.g. a momentary DB hiccup on
   one row) heals itself automatically instead of permanently and silently
   dropping that row. The tradeoff is that a row with a *persistent* parse
   failure (e.g. a malformed PDF row) will cause its file to retry forever
   without making progress, keeping that one file permanently "hot" in run
   logs every time the script executes. This is acceptable **only on the
   assumption that log-driven manual remediation is the team's intended
   model for City's persistent failures** — i.e. someone is expected to
   notice the repeating log line and fix the row/file by hand. If that
   assumption doesn't hold (e.g. nobody is watching the logs), a
   persistently malformed file degrades into silent noise rather than
   silent data loss, which is a different but still real problem this
   design does not solve.
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

## 6. Layout cross-check

Cross-checked against `docs/foundation-development-plan.md` §7 (Repo /
Folder Structure), the authoritative layout spec, not just inferred from
existing siblings:

- `src/core/ingestion_state.py` — fits the plan's `src/core/` bucket
  alongside `models/`, `db/`, `schemas/`, `normalization/`, `lifecycle/`,
  `geo/`. No new top-level package needed.
- `tests/unit/core/`, `tests/integration/` — both named explicitly in the
  plan's `tests/` tree.
- `scripts/ingest_galway_city.py` / `scripts/ingest_galway_county.py` —
  `scripts/` is not part of the plan's §7 tree (it predates this design,
  added later for `scaffold_tree.py`); kept consistent with that existing
  precedent rather than introducing a second scripts location.
- `config/galway/{city,county}.yaml` (consumed via `load_region_config`,
  unchanged by this design) — note the actual repo layout already diverges
  from the plan's original `config/authorities/galway_city.yaml` naming;
  this is a pre-existing, already-accepted deviation from Tasks 1-10, not
  something introduced by this design.

## 7. Testing

- `tests/unit/core/test_ingestion_state.py` (matches the existing
  `tests/unit/core/` sibling for `src/core/`): get/set watermark
  round-trip, is/mark file-ingested round-trip, against a real test
  Postgres, consistent with how `resolve_and_upsert` is already tested —
  no DB mocking.
- `tests/integration/test_ingest_galway_city.py` and
  `tests/integration/test_ingest_galway_county.py` (matches the existing
  `tests/integration/` convention used by
  `test_galway_city_pipeline_end_to_end.py`): full flow against test
  Postgres with a stubbed source (mock `discover`/`acquire` return values,
  real normalize/resolve/publish/state-write), asserting: watermark
  advances correctly past successes only; a forced failure on one record
  doesn't block others; a second run with the same stub input ingests
  nothing new (idempotency via watermark / file-tracking); City's
  self-healing retry actually re-attempts a file after a forced single-row
  failure followed by a clean run.
