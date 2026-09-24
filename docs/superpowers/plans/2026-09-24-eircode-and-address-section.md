# Eircode and Address Section Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every planning application a real, queryable `eircode` field
(extracted and backfilled from existing text), surface it and a cleaned
`site_address` in the UI and API, and wire it into the chat assistant so a
user asking about an Eircode gets a correct answer instead of silence.

**Architecture:** Add an `eircode` column to `applications` via an Alembic
migration. Extract it deterministically with a regex (already proven against
live data) inside the normalization pipeline for future ingests, and
backfill existing rows with a one-off SQL `UPDATE` using the same pattern.
Add `eircode` as a first-class filter in `application_service.search` (exact
match, normalized/no-space form) and teach `chat_service`'s LLM extraction
prompt to recognize an Eircode-shaped token in the user's question and route
it to that filter instead of dropping it into the free-text `q` search
(which we proved is fragile against spacing variance). Surface `eircode` and
`site_address` in the application detail page. (The search results table
deliberately does not gain an eircode column — see File Structure below —
this line originally overstated that scope; the detail page is correct.)

**Tech Stack:** Python 3.13, SQLAlchemy 2.0 + Alembic, PostgreSQL/PostGIS
(via `imresamu/postgis:16-3.4` in `docker-compose.yml`), FastAPI + Jinja2
templates, pytest, existing `qwen2.5:3b` local LLM via `LLMClient`.

**Spec:** This plan is self-contained; it implements the diagnosis already
established live against the database this session:
- Of 1,754 Galway City applications, 940 (53.6%) have a genuine Eircode
  embedded in `development_description`; Galway County has essentially none
  (9 of 20,805, 0.04%) because its ArcGIS `Location` field is just a
  townland name by design.
- The regex `H\d[A-Z\d] ?[A-Z0-9]{4}` (case-insensitive) reliably matches
  real Galway/Connacht routing keys (H53, H54, H61, H62, H65, H71, H91) in
  both spaced ("H91 WE0R") and unspaced ("H91WE0R") form, verified against
  live rows via `~*` in Postgres.
- The existing `_EIRCODE_RE` in `src/core/normalization/location.py` uses a
  narrower pattern (`\bH\d{2}\s*[A-Z0-9]{4}\b`) that Postgres's `~*`
  interprets differently at `\b` boundaries than Python's `re` does — this
  plan's regex is verified directly against Postgres, so it does not reuse
  that existing pattern as-is (see Task 1 for the exact final pattern used
  in both Python and SQL, kept identical on purpose).
- Chat's `q` search currently does a plain `ILIKE '%keyword%'` substring
  match with no space-normalization, which fails for ~45% of stored
  Eircodes because of formatting variance alone (confirmed: "H91WE0R" found
  a real row, "H91 WE0R" found zero, on data with mixed spacing).

## Global Constraints

- Canonical stored form for `eircode` is uppercase, no internal space (e.g.
  `H91WE0R`), 7 characters total (3-char routing key + 4-char unique
  identifier) — matches Eircode's own official format sans the space An
  Post's own tools display for readability.
- Do not touch `County` records differently from `City` — the same
  extraction function runs for both; County will simply backfill ~9 rows
  because that's the true count, not because of a special case.
- Do not remove or change the existing `q` free-text search behavior for
  non-Eircode terms — this plan is additive.
- All new SQL migrations must have a working `downgrade()`.
- Follow the existing test pattern in this repo: tests hit the real local
  Postgres directly via `SessionLocal()`, no mocking of the DB (see
  `tests/integration/test_application_service.py` and
  `tests/integration/test_chat_service.py` for the established style,
  including cleanup-by-prefix and `FakeLLMClient`).
- After any code file changes in a session, run `graphify update .` per
  this repo's `CLAUDE.md`, and commit `graphify-out/` alongside the code
  change in the same commit (already established convention in this repo's
  git history).

## Review Focus

- A question containing an Eircode AND a place name (e.g. "what's at H91
  WE0R in Salthill") — the extraction prompt must not silently drop the
  Eircode in favor of only extracting the place into `q`; both should be
  usable, but if only one can be trusted, the Eircode is the more precise
  signal and should win.
- A malformed/partial Eircode-looking token in the question (e.g. just
  "H91" alone, or "H9WE0R" with only one digit) — must not be treated as a
  valid Eircode filter; the routing-key format requires exactly one letter,
  two alphanumerics, then four alphanumerics (7 total), and a partial token
  should fall through to `q` instead of causing a filter that matches
  nothing.
- Case sensitivity — a user typing a lowercase Eircode ("h91 we0r") must
  match the same row as the uppercase stored form.
- An Eircode filter combined with zero results — must reuse the existing
  `_NO_MATCH_FOR_FILTERS_MESSAGE` / `_OUT_OF_COVERAGE_MESSAGE` distinction
  correctly rather than a new, inconsistent message, since Eircode is just
  another filter dimension, not a new answer-shape.
- Backfilling existing rows must not touch `application_events`
  (append-only event log) or trigger new event rows — the eircode backfill
  is a metadata correction on `applications` only, not a data re-ingestion.

---

## File Structure

- **Modify** `src/core/db/migrations/versions/0005_add_eircode_column.py`
  (new file) — Alembic migration adding `eircode` column + index to
  `applications`.
- **Modify** `src/core/models/application.py` — add `eircode` mapped column.
- **Modify** `src/core/schemas/application.py` — add `eircode` field to
  `ApplicationCreate`.
- **Modify** `src/core/normalization/location.py` — fix `_EIRCODE_RE` to the
  verified pattern and confirm it returns the canonical no-space form.
- **Modify** `src/pipelines/normalize.py` — wire `extract_location()`'s
  `eircode` result into the `ApplicationCreate` it builds for City rows.
- **Modify** `src/core/normalization/galway_county.py` — extract eircode
  from `Description` for County rows too (using the same helper), even
  though live data shows it's rare, so future or other-county data isn't
  silently dropped.
- **Modify** `src/pipelines/resolve.py` — no change expected (it already
  passes through all `ApplicationCreate` fields generically via
  `model_dump()`), but Task 3 verifies this holds for the new field.
- **Create** `scripts/backfill_eircode.py` — one-off backfill script for
  existing rows, mirroring the style of other one-off scripts in
  `scripts/`.
- **Modify** `src/services/application_service.py` — add `eircode` as a
  filter in `search()`.
- **Modify** `src/services/chat_service.py` — teach the extraction prompt
  about Eircode, add `eircode` to `_FILTER_KEYS`, add a deterministic
  Eircode-token detector as a safety net (small models are unreliable; the
  existing code already has several examples of "never trust the LLM alone,
  verify deterministically" — e.g. `_mentions_authority`,
  `_contains_application_ref`).
- **Modify** `src/web/templates/application_detail.html` — add an Eircode
  row.
- **Modify** `src/web/templates/partials/application_table.html` — no
  column added (table is already wide with 6 columns; Eircode belongs on
  the detail page, not the list, to avoid cramming). Confirmed as a
  deliberate choice, not an oversight — Task 7 documents this.
- **Test:** `tests/unit/core/test_normalize_location.py` (new, if it
  doesn't already exist — check first),
  `tests/unit/pipelines/test_normalize_galway_city.py` (extend),
  `tests/unit/pipelines/test_normalize_galway_county.py` (extend),
  `tests/integration/test_application_service.py` (extend),
  `tests/integration/test_chat_service.py` (extend).

---

### Task 1: Fix and verify the Eircode extraction regex

**Files:**
- Modify: `src/core/normalization/location.py:24,41-46`
- Test: `tests/unit/core/test_normalize_location.py` (check if this file
  already exists first — if not, create it; the function `extract_location`
  currently has no dedicated unit test file based on the repo's test
  listing)

**Interfaces:**
- Consumes: nothing new.
- Produces: `extract_eircode(text: str) -> str` — a public, testable
  function (currently private as `_extract_eircode`; Task 2 and Task 5 both
  need to call this from other modules, so it must be exported). Returns
  the canonical form `"H91WE0R"` (uppercase, no internal space) or `""` if
  no match. This is a behavior change from the current private function,
  which returns a spaced form (`"H91 WE0R"`) — the canonical form for
  storage and matching in this plan is unspaced; Task 6's UI display step
  formats it with a space for human readability only at render time.

- [ ] **Step 1: Check whether a location test file already exists**

Run: `ls tests/unit/core/test_normalize_location.py 2>&1`

If it exists, read it fully before proceeding and add to it rather than
overwriting. If it doesn't exist (expected, based on the current test
listing), create it fresh in Step 2.

- [ ] **Step 2: Write the failing tests**

Create `tests/unit/core/test_normalize_location.py`:

```python
import pytest

from src.core.normalization.location import extract_eircode


@pytest.mark.parametrize(
    "text,expected",
    [
        ("...Threadneedle Road Galway H91WE0R", "H91WE0R"),
        ("...Threadneedle Road Galway H91 WE0R", "H91WE0R"),
        ("...Salthill Galway h91we0r", "H91WE0R"),  # lowercase input
        ("EOD on 17/133 ... H91 1X08", "H91 1X08".replace(" ", "")),
        ("No eircode in this description at all", ""),
        ("", ""),
        ("Contains just H91 which is not a full eircode", ""),
        ("Partial H9WE0R is not valid (only one digit)", ""),
    ],
)
def test_extract_eircode(text, expected):
    assert extract_eircode(text) == expected


def test_extract_eircode_from_county_style_location_field():
    # County's Location field rarely has one, but when it does (9 of 20,805
    # live rows), it must still be found the same way as City's.
    assert extract_eircode("Shanbally, Craughwell, H91X3PN") == "H91X3PN"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/unit/core/test_normalize_location.py -v`
Expected: FAIL with `ImportError: cannot import name 'extract_eircode'`

- [ ] **Step 4: Fix the regex and rename to a public function**

In `src/core/normalization/location.py`, replace lines 24 and 41-46:

```python
_EIRCODE_RE = re.compile(r"H\d[A-Z\d] ?[A-Z0-9]{4}", re.IGNORECASE)
```

```python
def extract_eircode(text: str) -> str:
    if not text:
        return ""
    m = _EIRCODE_RE.search(text)
    if m:
        return m.group(0).upper().replace(" ", "")
    return ""
```

Update the `extract_location()` function (around line 37) to call the
renamed function:

```python
def extract_location(description: str) -> dict:
    if not description:
        return {"area": "", "address": "", "eircode": ""}
    return {
        "area": _extract_area(description),
        "address": _extract_address(description),
        "eircode": extract_eircode(description),
    }
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/unit/core/test_normalize_location.py -v`
Expected: All PASS

- [ ] **Step 6: Run the full existing test suite to check for regressions**

Run: `docker compose up -d && sleep 3 && source .venv/bin/activate && python -m pytest tests/unit -q`
Expected: all previously-passing tests still pass (this file was previously
untested directly, only indirectly through `test_normalize_galway_city.py`
via `extract_location`'s return dict, which is unaffected in shape).

- [ ] **Step 7: Commit**

```bash
git add src/core/normalization/location.py tests/unit/core/test_normalize_location.py
git commit -m "fix: correct eircode regex and export extract_eircode publicly"
```

---

### Task 2: Add `eircode` to the schema and ORM model

**Files:**
- Modify: `src/core/schemas/application.py`
- Modify: `src/core/models/application.py`
- Test: `tests/unit/core/test_application_schema.py` (existing file — read
  it first, then extend)

**Interfaces:**
- Consumes: nothing new from Task 1 directly (schema/model changes are
  independent of the regex fix).
- Produces: `ApplicationCreate.eircode: Optional[str] = None` and
  `Application.eircode: Mapped[str | None]` — Task 3 (normalize pipeline)
  and Task 4 (migration) both depend on this field existing under this
  exact name.

- [ ] **Step 1: Read the existing schema test file**

Run: `cat tests/unit/core/test_application_schema.py`

Understand its existing assertions before adding to them (per the plan's
File Structure note, this file already exists and is used elsewhere in the
repo — do not overwrite, extend).

- [ ] **Step 2: Write the failing test**

Add to `tests/unit/core/test_application_schema.py`:

```python
def test_application_create_accepts_eircode():
    from src.core.schemas.application import ApplicationCreate

    app = ApplicationCreate(
        planning_authority="Galway City Council",
        source_entity="GALWAY_CITY_COUNCIL",
        application_ref="24/0001",
        applicant_name="Test Applicant",
        development_description="test",
        application_type="PERMISSION",
        planning_status_current="Received",
        date_received="2026-01-01",
        source_system="test",
        source_file="test.pdf",
        eircode="H91WE0R",
    )
    assert app.eircode == "H91WE0R"


def test_application_create_eircode_defaults_to_none():
    from src.core.schemas.application import ApplicationCreate

    app = ApplicationCreate(
        planning_authority="Galway City Council",
        source_entity="GALWAY_CITY_COUNCIL",
        application_ref="24/0002",
        applicant_name="Test Applicant",
        development_description="test",
        application_type="PERMISSION",
        planning_status_current="Received",
        date_received="2026-01-01",
        source_system="test",
        source_file="test.pdf",
    )
    assert app.eircode is None
```

(If the existing file already has its own local imports/fixtures at the top
instead of importing inline, match that file's actual existing style
instead of the inline import shown here — read Step 1's output first.)

- [ ] **Step 3: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/unit/core/test_application_schema.py -v`
Expected: FAIL with a pydantic validation error (`eircode` not a recognized
field, since `ApplicationCreate` has `model_config = ConfigDict(extra="forbid")`)

- [ ] **Step 4: Add the field to the schema**

In `src/core/schemas/application.py`, add after the `site_geometry` line
(around line 24):

```python
    eircode: Optional[str] = None
```

- [ ] **Step 5: Add the column to the ORM model**

In `src/core/models/application.py`, add after the `site_geometry` line
(around line 28):

```python
    eircode: Mapped[str | None] = mapped_column(String, nullable=True)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/unit/core/test_application_schema.py -v`
Expected: All PASS

Note: this will fail at the ORM/DB level until Task 4's migration runs —
these are pure Pydantic/dataclass-level tests with no DB round-trip, so
they should pass now. Do not run integration tests yet.

- [ ] **Step 7: Commit**

```bash
git add src/core/schemas/application.py src/core/models/application.py tests/unit/core/test_application_schema.py
git commit -m "feat: add eircode field to ApplicationCreate schema and Application model"
```

---

### Task 3: Database migration to add the `eircode` column

**Files:**
- Create: `src/core/db/migrations/versions/0005_add_eircode_column.py`
- Test: `tests/integration/test_migration_applies.py` (existing file — read
  it first, then extend)

**Interfaces:**
- Consumes: `Application.eircode` from Task 2 (the ORM model must already
  declare this column so Alembic's migration matches the model).
- Produces: a live `eircode` column (nullable, indexed) on the `applications`
  table in Postgres — Task 4 (backfill), Task 5 (search filter), and Task 6
  (UI) all read/write this column directly via raw SQL or the ORM.

- [ ] **Step 1: Read the existing migration test file**

Run: `cat tests/integration/test_migration_applies.py`

- [ ] **Step 2: Write the failing test**

Add to `tests/integration/test_migration_applies.py` (matching that file's
existing style — it already asserts on `index_columns` per the earlier grep
in this session, e.g. `assert ("application_type",) in index_columns`):

```python
def test_eircode_column_exists_and_is_indexed():
    from sqlalchemy import inspect
    from src.core.db.session import engine

    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("applications")}
    assert "eircode" in columns

    indexes = inspector.get_indexes("applications")
    index_columns = {tuple(idx["column_names"]) for idx in indexes}
    assert ("eircode",) in index_columns
```

(Check the existing file's exact import path for `engine` — if it differs
from `src.core.db.session`, use whatever this file's own existing tests
already import. This detail must be confirmed by reading Step 1's output.)

- [ ] **Step 3: Run test to verify it fails**

Run: `docker compose up -d && sleep 3 && source .venv/bin/activate && python -m pytest tests/integration/test_migration_applies.py::test_eircode_column_exists_and_is_indexed -v`
Expected: FAIL — column does not exist yet

- [ ] **Step 4: Write the migration**

Create `src/core/db/migrations/versions/0005_add_eircode_column.py`:

```python
"""Add eircode column to applications

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-24

"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("eircode", sa.String(), nullable=True))
    op.create_index(
        "ix_applications_eircode",
        "applications",
        ["eircode"],
    )


def downgrade() -> None:
    op.drop_index("ix_applications_eircode", table_name="applications")
    op.drop_column("applications", "eircode")
```

Before finalizing, run `ls src/core/db/migrations/versions/` and open the
most recent migration's `down_revision` value to confirm `"0004"` is
correct (the plan's earlier repo inspection found `0004_create_dhlgh_applications.py`
as the latest at plan-writing time — verify this hasn't changed since).

- [ ] **Step 5: Apply the migration**

Run: `source .venv/bin/activate && alembic upgrade head`
Expected: migration `0005` applies cleanly with no errors

- [ ] **Step 6: Run test to verify it passes**

Run: `source .venv/bin/activate && python -m pytest tests/integration/test_migration_applies.py::test_eircode_column_exists_and_is_indexed -v`
Expected: PASS

- [ ] **Step 7: Verify downgrade works cleanly, then re-upgrade**

Run:
```bash
alembic downgrade -1
alembic upgrade head
```
Expected: both commands succeed with no errors; re-running the test from
Step 6 still passes after re-upgrading.

- [ ] **Step 8: Commit**

```bash
git add src/core/db/migrations/versions/0005_add_eircode_column.py tests/integration/test_migration_applies.py
git commit -m "feat: add database migration for eircode column"
```

---

### Task 4: Wire eircode extraction into the normalization pipeline

**Files:**
- Modify: `src/pipelines/normalize.py`
- Modify: `src/core/normalization/galway_county.py`
- Test: `tests/unit/pipelines/test_normalize_galway_city.py` (extend)
- Test: `tests/unit/pipelines/test_normalize_galway_county.py` (extend)

**Interfaces:**
- Consumes: `extract_eircode(text: str) -> str` from Task 1;
  `ApplicationCreate.eircode` from Task 2.
- Produces: `normalize_row()` (City) and `normalize_county_row()` (County)
  both populate `eircode` on the `ApplicationCreate` they return — Task 5's
  backfill script and Task 6's `search()` both rely on future ingests
  populating this field automatically (not just the one-off backfill).

- [ ] **Step 1: Write the failing test for City normalization**

Add to `tests/unit/pipelines/test_normalize_galway_city.py`:

```python
def test_normalize_row_extracts_eircode_from_description():
    raw_row = {
        "file_number": "24/0001",
        "applicant": "Test Applicant",
        "app_type": "P",
        "description": "New dwelling at 12 Lioscarraig Threadneedle Road Galway H91WE0R",
    }
    app = normalize_row(raw_row, source_type="received", region_config=REGION_CONFIG,
                        source_file="test.pdf")
    assert app.eircode == "H91WE0R"


def test_normalize_row_eircode_is_none_when_absent():
    raw_row = {
        "file_number": "24/0002",
        "applicant": "Test Applicant",
        "app_type": "P",
        "description": "New dwelling with no postcode mentioned",
    }
    app = normalize_row(raw_row, source_type="received", region_config=REGION_CONFIG,
                        source_file="test.pdf")
    assert app.eircode is None
```

- [ ] **Step 2: Write the failing test for County normalization**

Add to `tests/unit/pipelines/test_normalize_galway_county.py`:

```python
def test_normalize_county_row_extracts_eircode_when_present():
    raw_row = {
        "OBJECTID": 999001,
        "ApplicationNumber": "26/9998",
        "ApplicantName": "Test Applicant",
        "ApplicationType": "PERMISSION",
        "ApplicationStatus": "Application Pending",
        "ReceivedDate": "03/03/2026",
        "Decision": "n\\a",
        "Location": "Shanbally, Craughwell, H91X3PN",
        "Description": "New dwelling at Craughwell",
    }
    app = normalize_county_row(raw_row, region_config=REGION_CONFIG, source_file="arcgis:999001")
    assert app.eircode == "H91X3PN"


def test_normalize_county_row_eircode_is_none_when_absent():
    raw_row = {
        "OBJECTID": 999002,
        "ApplicationNumber": "26/9997",
        "ApplicantName": "Test Applicant",
        "ApplicationType": "PERMISSION",
        "ApplicationStatus": "Application Pending",
        "ReceivedDate": "03/03/2026",
        "Decision": "n\\a",
        "Location": "Oranmore",
        "Description": "New dwelling",
    }
    app = normalize_county_row(raw_row, region_config=REGION_CONFIG, source_file="arcgis:999002")
    assert app.eircode is None
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/unit/pipelines/test_normalize_galway_city.py::test_normalize_row_extracts_eircode_from_description tests/unit/pipelines/test_normalize_galway_county.py::test_normalize_county_row_extracts_eircode_when_present -v`
Expected: FAIL — `app.eircode` is not set (currently absent from the
`ApplicationCreate(...)` call sites), so it defaults to `None` even when
present in the description.

Wait — this may actually show as "AttributeError" only if Task 2 wasn't
completed; if Task 2 is done, this assert fails because the code hasn't
been wired yet (`app.eircode` will be `None` even when it should be found)
rather than raising `AttributeError`. Confirm the actual failure by reading
the pytest output.

- [ ] **Step 4: Wire eircode into City's normalize_row**

In `src/pipelines/normalize.py`, the function already calls
`extract_location(description)` internally to get `location = extract_location(description)`
(see line 48 of the existing file, already computing `location["address"]`
and `location["area"]`). Add `eircode=location["eircode"] or None,` to the
`ApplicationCreate(...)` constructor call (after the `site_locality=` line,
around line 59), matching the returned dict key already present but
currently unused for `eircode`. Note: `extract_location()`'s returned dict
key is `"eircode"` and, after Task 1, is already the canonical no-space
uppercase form.

- [ ] **Step 5: Wire eircode into County's normalize_county_row**

In `src/core/normalization/galway_county.py`, add the import at the top:

```python
from src.core.normalization.location import extract_eircode
```

Then in `normalize_county_row()`, after the `description = _clean_str(raw_row.get("Description")) or ""`
line (line 37), add:

```python
    location_text = _clean_str(raw_row.get("Location")) or ""
    eircode = extract_eircode(location_text) or extract_eircode(description) or None
```

Add `eircode=eircode,` to the `ApplicationCreate(...)` constructor call
(after the `site_address=` line, around line 47).

(Checking both `Location` and `Description` fields for County is
deliberate: the live audit found County Eircodes appear incidentally in
whichever free-text field the data-entry person used, not consistently in
one or the other.)

- [ ] **Step 6: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/unit/pipelines/test_normalize_galway_city.py tests/unit/pipelines/test_normalize_galway_county.py -v`
Expected: All PASS (including all pre-existing tests in both files — no
regressions)

- [ ] **Step 7: Run the full unit suite**

Run: `source .venv/bin/activate && python -m pytest tests/unit -q`
Expected: all pass

- [ ] **Step 8: Commit**

```bash
git add src/pipelines/normalize.py src/core/normalization/galway_county.py tests/unit/pipelines/test_normalize_galway_city.py tests/unit/pipelines/test_normalize_galway_county.py
git commit -m "feat: extract eircode during City and County normalization"
```

---

### Task 5: Backfill eircode for existing rows

**Files:**
- Create: `scripts/backfill_eircode.py`
- Test: none (this is a one-off data-repair script, consistent with
  `scripts/enrich_from_dhlgh.py` and `scripts/backfill_galway_city_chunked.py`
  already in this repo, which also lack dedicated test files — verify by
  running `ls tests/ -R | grep -i backfill` before assuming; if a backfill
  test pattern exists elsewhere in this repo, follow it instead)

**Interfaces:**
- Consumes: `extract_eircode()` from Task 1; the live `eircode` column from
  Task 3.
- Produces: `eircode` populated on all pre-existing rows where the pattern
  is found in `development_description` — no new interface for later tasks,
  this is a terminal data-repair step.

- [ ] **Step 1: Check for an existing backfill test pattern**

Run: `ls tests/ -R | grep -i backfill`

If a pattern exists (e.g. a test that runs the backfill against seeded rows
and asserts the result), follow that pattern for this task's script
instead of the untested one-off approach below. If none exists (expected,
per this plan's File Structure), proceed with Steps 2+.

- [ ] **Step 2: Write the backfill script**

`scripts/enrich_from_dhlgh.py` uses the SQLAlchemy ORM (`select`, `func`)
rather than raw SQL strings — match that convention here, not raw
`session.execute("SELECT ...")`.

Create `scripts/backfill_eircode.py`:

```python
"""
One-off backfill: populate applications.eircode for existing rows by
re-running the same extract_eircode() regex used during normalization
against development_description. Safe to re-run (idempotent — only ever
sets eircode, never clears a value that was already correctly set by a
newer ingest).
"""

import logging

from sqlalchemy import select

from src.core.db.session import SessionLocal
from src.core.models.application import Application
from src.core.normalization.location import extract_eircode

logger = logging.getLogger(__name__)


def run_backfill(dry_run: bool = False) -> dict:
    session = SessionLocal()
    try:
        rows = session.scalars(
            select(Application).where(Application.eircode.is_(None))
        ).all()

        updated = 0
        for application in rows:
            eircode = extract_eircode(application.development_description or "")
            if eircode:
                if not dry_run:
                    application.eircode = eircode
                updated += 1

        if not dry_run:
            session.commit()

        logger.info(
            "Eircode backfill complete: scanned=%d updated=%d dry_run=%s",
            len(rows), updated, dry_run,
        )
        return {"scanned": len(rows), "updated": updated}
    finally:
        session.close()


def main() -> None:
    import argparse

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Backfill eircode for existing applications.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = run_backfill(dry_run=args.dry_run)
    print(result)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Dry-run the backfill against live data**

Run: `docker compose up -d && sleep 3 && source .venv/bin/activate && python scripts/backfill_eircode.py --dry-run`
Expected output: `{'scanned': <some number close to 22559>, 'updated': <a number close to 949 (940 City + 9 County, per this plan's live-verified counts)>}`

If the `updated` count differs significantly from ~949, stop and
investigate before proceeding — it likely means either the regex changed
behavior between Task 1 and this backfill, or new data was ingested since
this plan was written (both are fine to proceed past if understood, but
should not be silently ignored).

- [ ] **Step 4: Run the backfill for real**

Run: `source .venv/bin/activate && python scripts/backfill_eircode.py`
Expected: same `updated` count as the dry run, `dry_run: False` in the log line.

- [ ] **Step 5: Verify the backfill in the database**

Run:
```bash
docker exec planning-intelligence-postgres-1 psql -U planning -d planning_intelligence -c "SELECT planning_authority, count(*) FROM applications WHERE eircode IS NOT NULL GROUP BY 1;"
```
Expected: two rows, City count near 940, County count near 9 (matching
Step 3's dry run).

- [ ] **Step 6: Commit**

```bash
git add scripts/backfill_eircode.py
git commit -m "feat: backfill eircode for existing applications from description text"
```

---

### Task 6: Add `eircode` as a search filter

**Files:**
- Modify: `src/services/application_service.py`
- Test: `tests/integration/test_application_service.py` (extend)

**Interfaces:**
- Consumes: `Application.eircode` column from Task 3.
- Produces: `search(db, filters, page, page_size)` now recognizes an
  `"eircode"` key in `filters` — Task 7 (chat service) depends on this
  filter key existing under this exact name.

- [ ] **Step 1: Write the failing test**

Add to `tests/integration/test_application_service.py`. First, extend the
`_insert` helper to accept an optional `eircode` parameter (read the
existing helper at the top of this file first, since it currently doesn't
have an eircode column in its INSERT statement — this INSERT will need
`eircode` added to both the column list and the VALUES/params, defaulting
to `None`):

```python
def _insert(session, ref, authority, status, app_type, received, applicant, address, description, eircode=None):
    session.execute(
        text(
            """
            INSERT INTO applications (
                id, planning_authority, source_entity, application_ref,
                applicant_name, site_address, development_description,
                application_type, planning_status_current, date_received,
                source_system, source_file, source_ingested_at,
                further_information_flag, protected_structure_flag,
                eia_eis_flag, other_regulatory_flags, commuter_belt_flag,
                raw_payload_json, eircode
            ) VALUES (
                gen_random_uuid(), :authority, :authority, :ref,
                :applicant, :address, :description, :app_type, :status,
                :received, 'TEST', 'test.pdf', now(),
                false, false, false, '{}', false, '{}', :eircode
            )
            """
        ),
        {
            "authority": authority,
            "ref": ref,
            "applicant": applicant,
            "address": address,
            "description": description,
            "app_type": app_type,
            "status": status,
            "received": received,
            "eircode": eircode,
        },
    )
```

Then add a new test:

```python
def test_search_filters_by_eircode():
    _cleanup()
    session = SessionLocal()
    try:
        _insert(
            session, f"{PREFIX}/0003", "Galway City Council", "Received", "Permission",
            date(2026, 3, 1), "Carol Example", "5 High Street, Galway",
            "New extension (APPSVCTEST)", eircode="H91WE0R",
        )
        session.commit()
    finally:
        session.close()

    try:
        session = SessionLocal()
        try:
            rows, total = search(session, {"eircode": "H91WE0R"}, page=1, page_size=25)
        finally:
            session.close()
        refs = {r.application_ref for r in rows}
        assert f"{PREFIX}/0003" in refs
        assert total == 1
    finally:
        _cleanup()


def test_search_filters_by_eircode_case_and_space_insensitive():
    _cleanup()
    session = SessionLocal()
    try:
        _insert(
            session, f"{PREFIX}/0004", "Galway City Council", "Received", "Permission",
            date(2026, 3, 1), "Dave Example", "6 High Street, Galway",
            "New extension (APPSVCTEST)", eircode="H91WE0R",
        )
        session.commit()
    finally:
        session.close()

    try:
        session = SessionLocal()
        try:
            rows, total = search(session, {"eircode": "h91 we0r"}, page=1, page_size=25)
        finally:
            session.close()
        refs = {r.application_ref for r in rows}
        assert f"{PREFIX}/0004" in refs
    finally:
        _cleanup()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/integration/test_application_service.py::test_search_filters_by_eircode tests/integration/test_application_service.py::test_search_filters_by_eircode_case_and_space_insensitive -v`
Expected: FAIL — `eircode` filter is currently ignored by `search()`, so
both would return 0 results instead of the expected match (the second
would additionally fail even with a naive equality filter, since the input
has different casing/spacing than the stored value).

- [ ] **Step 3: Add the filter to search()**

In `src/services/application_service.py`, add after the
`date_received_to` block (around line 39):

```python
    eircode = filters.get("eircode")
    if eircode:
        normalized = eircode.strip().upper().replace(" ", "")
        query = query.filter(Application.eircode == normalized)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/integration/test_application_service.py -v`
Expected: All PASS (including all pre-existing tests in this file)

- [ ] **Step 5: Commit**

```bash
git add src/services/application_service.py tests/integration/test_application_service.py
git commit -m "feat: add eircode as a search filter, normalized for case and spacing"
```

---

### Task 7: Teach the chat assistant to recognize Eircode questions

**Files:**
- Modify: `src/services/chat_service.py`
- Test: `tests/integration/test_chat_service.py` (extend)

**Interfaces:**
- Consumes: `search()`'s new `"eircode"` filter key from Task 6.
- Produces: `answer_question()` now correctly answers Eircode-shaped
  questions — this is the final user-facing behavior this plan delivers;
  no later task depends on this task's internals.

- [ ] **Step 1: Write the failing tests**

Add to `tests/integration/test_chat_service.py`. First add a helper to seed
a row with an eircode (matching the existing `_seed()` style, but as a
separate function so it doesn't interfere with other tests using `_seed()`):

```python
def _seed_with_eircode(eircode="H91WE0R"):
    session = SessionLocal()
    try:
        session.execute(
            text(
                """
                INSERT INTO applications (
                    id, planning_authority, source_entity, application_ref,
                    applicant_name, site_address, development_description,
                    application_type, planning_status_current, date_received,
                    source_system, source_file, source_ingested_at,
                    further_information_flag, protected_structure_flag,
                    eia_eis_flag, other_regulatory_flags, commuter_belt_flag,
                    raw_payload_json, eircode
                ) VALUES (
                    gen_random_uuid(), 'Galway City Council', 'GALWAY_CITY_COUNCIL',
                    :ref, 'Jane Example', 'Threadneedle Road, Galway', 'New extension',
                    'Permission', 'Granted', :received,
                    'TEST', 'test.pdf', :ingested_at,
                    false, false, false, '{}', false, '{}', :eircode
                )
                """
            ),
            {
                "ref": f"{PREFIX}/0002",
                "received": date(2026, 3, 1),
                "ingested_at": datetime(2026, 3, 2, 9, 0),
                "eircode": eircode,
            },
        )
        session.commit()
    finally:
        session.close()
```

Then add the tests:

```python
def test_answer_question_finds_application_by_eircode():
    _cleanup()
    _seed_with_eircode()
    try:
        session = SessionLocal()
        try:
            client = FakeLLMClient(replies=['{"eircode": "H91WE0R"}'])
            result = answer_question(session, "What's at H91 WE0R?", client=client)
        finally:
            session.close()

        assert result["total"] == 1
        assert result["applications"][0].application_ref == f"{PREFIX}/0002"
        assert result["filters"]["eircode"] == "H91WE0R"
    finally:
        _cleanup()


def test_answer_question_normalizes_llm_extracted_eircode_spacing():
    _cleanup()
    _seed_with_eircode()
    try:
        session = SessionLocal()
        try:
            # The LLM may echo the eircode back with the same spacing the
            # user typed it with -- the filter itself must normalize this,
            # not rely on the LLM to have done so.
            client = FakeLLMClient(replies=['{"eircode": "H91 WE0R"}'])
            result = answer_question(session, "What's at H91 WE0R?", client=client)
        finally:
            session.close()

        assert result["total"] == 1
    finally:
        _cleanup()


def test_answer_question_drops_malformed_eircode_like_token():
    _cleanup()
    _seed_with_eircode()
    try:
        session = SessionLocal()
        try:
            # "H91" alone is not a complete eircode (routing key only, no
            # unique identifier half) -- if the LLM hallucinates this into
            # the eircode field, applying it as an exact-match filter would
            # match nothing even though the real row (with a full eircode)
            # exists, silently hiding a true match. Must be dropped so the
            # question falls through to an unfiltered/q-based search instead.
            client = FakeLLMClient(replies=['{"eircode": "H91", "q": "threadneedle"}'])
            result = answer_question(session, "Anything near H91?", client=client)
        finally:
            session.close()

        assert "eircode" not in result["filters"]
        assert result["total"] == 1
        assert result["applications"][0].application_ref == f"{PREFIX}/0002"
    finally:
        _cleanup()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/integration/test_chat_service.py::test_answer_question_finds_application_by_eircode tests/integration/test_chat_service.py::test_answer_question_normalizes_llm_extracted_eircode_spacing tests/integration/test_chat_service.py::test_answer_question_drops_malformed_eircode_like_token -v`
Expected: FAIL — `eircode` is not in `_FILTER_KEYS`, so `_extract_filters`
silently drops it before it ever reaches `search()`.

- [ ] **Step 3: Add eircode to the allowed filter keys**

In `src/services/chat_service.py`, modify `_FILTER_KEYS` (line 33):

```python
_FILTER_KEYS = (
    "planning_authority",
    "planning_status_current",
    "application_type",
    "date_received_from",
    "date_received_to",
    "eircode",
    "q",
)
```

- [ ] **Step 4: Update the extraction prompt to teach the model about Eircode**

In `_extraction_prompt()` (around line 47-101), add a new allowed key to
the key list (after the `"q":` line, around line 59-61):

```python
        '  "eircode": an Irish Eircode if the question mentions one (e.g. "H91 WE0R" '
        'or "H91WE0R") -- a 7-character routing key + unique identifier pair, always '
        "starting with a letter followed by 2 alphanumerics, then 4 more alphanumerics, "
        "optionally separated by a space. Extract it exactly as written; do not guess one "
        "from a place name.\n\n"
```

Add a worked example (after the existing examples, before the closing of
the function, around line 100):

```python
        '  Question: "What\'s at H91 WE0R?"\n'
        '  Reply: {"eircode": "H91 WE0R"}\n'
```

- [ ] **Step 5: Add deterministic validation for the extracted eircode**

In `_extract_filters()` (around line 104-142), add a validation step
following the same "never trust the LLM's guess alone" pattern already
used for `planning_authority` and `planning_status_current` in this
function. Add this near the other cleanup checks (after the
`date_received_from`/`date_received_to` validation block, around line 127):

```python
    if "eircode" in filters and not _is_valid_eircode(filters["eircode"]):
        del filters["eircode"]
```

Add the validator function near `_is_valid_iso_date` (around line 165-170):

```python
_EIRCODE_VALIDATION_RE = re.compile(r"^[A-Z]\d[A-Z0-9]\s?[A-Z0-9]{4}$")


def _is_valid_eircode(value: str) -> bool:
    return bool(_EIRCODE_VALIDATION_RE.match(value.strip().upper()))
```

(This validation pattern intentionally matches the full 7-character
Eircode shape, not the looser `_EIRCODE_RE` in `location.py` used for
free-text extraction — here we're validating a value the LLM already
isolated, not searching for one inside a longer string, so anchoring with
`^`/`$` is correct and prevents "H91" alone or "H91WE0R123" from passing.)

- [ ] **Step 6: Normalize the eircode before it reaches search()**

Still in `_extract_filters()`, after the validation step from Step 5,
normalize the surviving value so `search()` (Task 6) always receives the
canonical form regardless of what the LLM echoed back:

```python
    if "eircode" in filters:
        filters["eircode"] = filters["eircode"].strip().upper().replace(" ", "")
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/integration/test_chat_service.py -v`
Expected: All PASS (including all pre-existing tests in this file — no
regressions to the existing authority/status/type/ref guessing guards)

- [ ] **Step 8: Run the full test suite**

Run: `source .venv/bin/activate && python -m pytest tests/unit tests/integration -q`
Expected: all pass

- [ ] **Step 9: Commit**

```bash
git add src/services/chat_service.py tests/integration/test_chat_service.py
git commit -m "feat: recognize and validate eircode in chat question extraction"
```

---

### Task 8: Surface eircode and address in the UI

**Files:**
- Modify: `src/web/templates/application_detail.html`
- Test: `tests/integration/test_web_routes.py` (existing file — read first,
  then extend if it covers this route; if this route isn't covered by an
  existing integration test, add one matching that file's existing style)

**Interfaces:**
- Consumes: `application.eircode` (already present on any `Application` ORM
  object fetched from the DB, once Task 3's migration has run — no new
  service-layer changes needed, this is a template-only task).
- Produces: nothing new for later tasks — this is the final user-facing
  step.

- [ ] **Step 1: Read the existing web routes test file**

Run: `cat tests/integration/test_web_routes.py`

This file already has a working detail-page test,
`test_detail_page_shows_all_expected_fields()`, backed by a `_seed_detail()`
helper (uses `TestClient` from `fastapi.testclient`, prefix `DETAIL_PREFIX`,
raw `text()`-wrapped SQL INSERT). Extend `_seed_detail()`'s INSERT statement
to also set `eircode`, and extend the existing test's assertions — do not
write a new seed helper or a new test function from scratch.

- [ ] **Step 2: Write the failing test**

In `_seed_detail()`'s INSERT statement, add `eircode` to both the column
list and the VALUES clause (using a literal `'H91WE0R'` value rather than a
bound parameter, consistent with this INSERT's existing mix of literals and
`:params`), then add to `test_detail_page_shows_all_expected_fields()`'s
list of expected substrings:

```python
"H91 WE0R",  # eircode displayed with a space for readability
```

(This assumes Task 8 Step 4's template renders the stored `"H91WE0R"` as
`"H91 WE0R"` — if the template instead displays the raw unspaced form,
adjust this assertion to `"H91WE0R"` to match whatever Step 4 actually
implements.)

- [ ] **Step 3: Run test to verify it fails**

Run: `docker compose up -d && sleep 3 && source .venv/bin/activate && python -m pytest tests/integration/test_web_routes.py -k eircode -v`
Expected: FAIL — "Eircode" label not present in the current template output

- [ ] **Step 4: Add the Eircode row to the detail template**

In `src/web/templates/application_detail.html`, add a new row after the
"Site county" row (after line 16):

```html
    <tr><th>Eircode</th><td>{% if application.eircode %}{{ application.eircode[:3] }} {{ application.eircode[3:] }}{% else %}Not available{% endif %}</td></tr>
```

(Displaying with a space for readability — `"H91WE0R"` renders as
`"H91 WE0R"` — while the stored/queried form stays canonical/unspaced per
this plan's Global Constraints. This is a presentation-only transform, not
a data change.)

- [ ] **Step 5: Run test to verify it passes**

Run: `source .venv/bin/activate && python -m pytest tests/integration/test_web_routes.py -k eircode -v`
Expected: PASS

- [ ] **Step 6: Run the full test suite one final time**

Run: `source .venv/bin/activate && python -m pytest tests/unit tests/integration -q`
Expected: all pass

- [ ] **Step 7: Update graphify and commit**

```bash
graphify update .
git add src/web/templates/application_detail.html tests/integration/test_web_routes.py graphify-out/
git commit -m "feat: display eircode on the application detail page"
```

(If `graphify update .` is not available in this environment — check with
`which graphify` first — skip this step and note it to the user, consistent
with how earlier sessions in this repo handled the same situation.)

---

## Post-plan note: the Eircode Finder website

This plan deliberately does not integrate `https://finder.eircode.ie/#/` —
that's a manual/interactive lookup tool (address in, Eircode out), not an
API, so it can't be called programmatically from this pipeline without
either browser automation (fragile, against a third-party site's likely
terms of use) or a paid An Post GeoDirectory API key (already researched
and flagged as a cost in `docs/research/eircode_research_prompt.md`).

Once this plan ships, the practical next step for the "gray" (no Eircode,
no usable address) and "red" (has Eircode, not yet geocoded to
coordinates) records from the earlier map work is a separate, explicitly
scoped follow-up: either (a) a person manually looks up ambiguous addresses
on the Eircode Finder website for a small, high-value subset, or (b) a
paid GeoDirectory API integration once the project has funding — which is
exactly the pitch angle this whole thread has been building toward.
