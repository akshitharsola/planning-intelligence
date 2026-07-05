# County Stack Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the two correctness bugs and the missing-index gap identified by
independent review of the Galway County ingestion → storage → answering
stack, without changing its overall architecture.

**Architecture:** All work happens on the `worktree-web-dashboard` branch
(worktree at `.claude/worktrees/web-dashboard`), which already contains
`application_service.py`, the chat layer, and the alembic migrations
(identical to `main` as of this writing). Three independent fixes:
1. `_derive_status` in county normalization must never silently invent a
   status for unrecognized vocabulary, and must consult the appeal fields
   that are already fetched but currently ignored.
2. `normalize_county_row` must reject a record with a blank/missing
   `ApplicationNumber` instead of silently coercing it to `""`, since
   `application_ref` is half of the natural key used for upsert dedup.
3. Add a migration with btree indexes on `planning_status_current`,
   `application_type`, `date_received`, plus `pg_trgm` GIN indexes on the
   three ILIKE-searched text columns.

**Tech Stack:** Python 3.11, SQLAlchemy 2.x ORM, Alembic migrations,
PostgreSQL + PostGIS (via `postgis/postgis:16-3.4` Docker image), pytest.

## Global Constraints

- Working directory for all commands: `/Users/akshitharsola/Documents/AiAgentic/planning-intelligence/.claude/worktrees/web-dashboard`
- Activate the venv first: `source .venv/bin/activate`
- Docker Postgres must be running: `docker compose ps` (from repo root) should show `planning-intelligence-postgres-1` as `Up`. If not: `docker compose up -d` from `/Users/akshitharsola/Documents/AiAgentic/planning-intelligence`.
- Follow TDD: write the failing test, run it, watch it fail for the right reason, then implement.
- Every task ends with the full test suite green: `python -m pytest`.
- After each commit, run `graphify update .` and stage `graphify-out/` alongside the code change in the same commit (per this repo's `CLAUDE.md`).
- Do not modify `main` — all commits land on `worktree-web-dashboard`.

---

### Task 1: Reject unrecognized status vocabulary instead of silently defaulting to "Received"

**Files:**
- Modify: `src/core/normalization/galway_county.py:73-91` (the `_derive_status` function)
- Test: `tests/unit/pipelines/test_normalize_galway_county.py`

**Interfaces:**
- Consumes: nothing new. Confirmed via `grep -rn "_derive_status"` that the only call site is inside `galway_county.py` itself (the `normalize_county_row` function) — no other module imports or calls it, so the signature change below is fully contained to this one file.
- Produces: `_derive_status(application_status, decision, appeal_decision=None) -> tuple[str, str]` — adds one new optional third parameter and keeps the same return shape (`(status, event_type)`).

**The one decision rule this task implements** (evaluate top to bottom, first match wins):

| # | Condition | Result |
|---|-----------|--------|
| 1 | `decision` cleaned is non-blank AND contains `"grant"` | `("Granted", "DECISION_GRANTED")` |
| 2 | `decision` cleaned is non-blank AND contains `"refus"` | `("Refused", "DECISION_REFUSED")` |
| 3 | `decision` cleaned is non-blank AND `appeal_decision` cleaned contains `"grant"` | `("Granted", "DECISION_GRANTED")` |
| 4 | `decision` cleaned is non-blank AND `appeal_decision` cleaned contains `"refus"` | `("Refused", "DECISION_REFUSED")` |
| 5 | `decision` cleaned is non-blank AND none of rows 1-4 matched | `("Unknown/Needs Review", "STATUS_UNRECOGNIZED")` — **this is the bug fix**: today this case silently falls through to `("Received", "APPLICATION_RECEIVED")`, misreporting a record that already has a real decision outcome the code just doesn't recognize |
| 6 | `decision` cleaned is blank AND `application_status` cleaned contains `"withdraw"` | `("Withdrawn", "APPLICATION_WITHDRAWN")` |
| 7 | `decision` cleaned is blank AND `application_status` cleaned contains `"incomplete"` | `("Invalid", "APPLICATION_INVALID")` |
| 8 | none of the above matched (includes the existing `"Application Pending"` case, which has no `Decision`) | `("Received", "APPLICATION_RECEIVED")` — unchanged from today, do not regress `test_normalize_county_row_received` |

Row 5 is the only new fallback behavior; rows 6-8 are the existing logic, untouched.

- [ ] **Step 1: Write the failing tests**

Add these three test functions to the end of `tests/unit/pipelines/test_normalize_galway_county.py`:

```python
def test_normalize_county_row_appeal_granted():
    raw_row = {
        "OBJECTID": 2,
        "ApplicationNumber": "20/2",
        "ApplicantName": "Test Applicant",
        "ApplicationType": "PERMISSION",
        "ApplicationStatus": "Application Finalised",
        "ReceivedDate": "01/01/2020",
        "Decision": "n\\a",
        "AppealDecision": "Grant Permission",
        "Location": "Athenry",
        "Description": "test",
    }
    app = normalize_county_row(raw_row, region_config=REGION_CONFIG, source_file="arcgis:2")
    assert app.planning_status_current == "Granted"
    assert app.status_event_type == "DECISION_GRANTED"


def test_normalize_county_row_appeal_refused():
    raw_row = {
        "OBJECTID": 3,
        "ApplicationNumber": "20/3",
        "ApplicantName": "Test Applicant",
        "ApplicationType": "PERMISSION",
        "ApplicationStatus": "Application Finalised",
        "ReceivedDate": "01/01/2020",
        "Decision": "n\\a",
        "AppealDecision": "Refuse Permission",
        "Location": "Athenry",
        "Description": "test",
    }
    app = normalize_county_row(raw_row, region_config=REGION_CONFIG, source_file="arcgis:3")
    assert app.planning_status_current == "Refused"
    assert app.status_event_type == "DECISION_REFUSED"


def test_normalize_county_row_unrecognized_decision_flags_for_review():
    # Deliberately does NOT contain "grant" or "refus" as a substring (unlike
    # e.g. "Part Grant Part Refusal", which would false-match the existing
    # grant/refuse checks) — this must be a decision string with no
    # recognized outcome word at all, to genuinely exercise the fallback.
    raw_row = {
        "OBJECTID": 4,
        "ApplicationNumber": "20/4",
        "ApplicantName": "Test Applicant",
        "ApplicationType": "PERMISSION",
        "ApplicationStatus": "Application Finalised",
        "ReceivedDate": "01/01/2020",
        "Decision": "Referred Back To Planning Authority",
        "Location": "Athenry",
        "Description": "test",
    }
    app = normalize_county_row(raw_row, region_config=REGION_CONFIG, source_file="arcgis:4")
    assert app.planning_status_current == "Unknown/Needs Review"
    assert app.status_event_type == "STATUS_UNRECOGNIZED"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/unit/pipelines/test_normalize_galway_county.py -v`

Expected: the three new tests FAIL. `test_normalize_county_row_appeal_granted` and `test_normalize_county_row_appeal_refused` fail because `_derive_status` currently returns `("Received", "APPLICATION_RECEIVED")` for these inputs (no appeal handling exists). `test_normalize_county_row_unrecognized_decision_flags_for_review` fails because there's currently no `"Unknown/Needs Review"` branch — it also returns `("Received", "APPLICATION_RECEIVED")`.

- [ ] **Step 3: Implement `_derive_status` with appeal handling and the unrecognized-decision fallback**

Replace the `_derive_status` function in `src/core/normalization/galway_county.py` (currently lines 73-91) with:

```python
def _derive_status(application_status, decision, appeal_decision=None) -> tuple[str, str]:
    decision_clean = _clean_str(decision)
    status_clean = _clean_str(application_status)
    appeal_clean = _clean_str(appeal_decision)

    if decision_clean:
        decision_lower = decision_clean.lower()
        if "grant" in decision_lower:
            return "Granted", "DECISION_GRANTED"
        if "refus" in decision_lower:
            return "Refused", "DECISION_REFUSED"
        if appeal_clean:
            appeal_lower = appeal_clean.lower()
            if "grant" in appeal_lower:
                return "Granted", "DECISION_GRANTED"
            if "refus" in appeal_lower:
                return "Refused", "DECISION_REFUSED"
        return "Unknown/Needs Review", "STATUS_UNRECOGNIZED"

    if status_clean:
        status_lower = status_clean.lower()
        if "withdraw" in status_lower:
            return "Withdrawn", "APPLICATION_WITHDRAWN"
        if "incomplete" in status_lower:
            return "Invalid", "APPLICATION_INVALID"

    return "Received", "APPLICATION_RECEIVED"
```

Then update the call site in `normalize_county_row` (currently lines 27-29 of the same file):

```python
    status, event_type = _derive_status(
        raw_row.get("ApplicationStatus"), raw_row.get("Decision"), raw_row.get("AppealDecision")
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/unit/pipelines/test_normalize_galway_county.py -v`

Expected: all 6 tests PASS (3 pre-existing + 3 new).

- [ ] **Step 5: Run the full suite to check for regressions**

Run: `source .venv/bin/activate && python -m pytest`

Expected: all tests pass, same count as before plus 3.

- [ ] **Step 6: Update graphify and commit**

```bash
graphify update .
git add src/core/normalization/galway_county.py tests/unit/pipelines/test_normalize_galway_county.py graphify-out/
git commit -m "$(cat <<'EOF'
fix: stop county normalization silently defaulting unrecognized decisions to Received

_derive_status previously fell through to "Received" for any Decision
value it didn't recognize (e.g. split/appeal outcomes), producing wrong
answers with no error signal. Now: a present, non-blank Decision that
doesn't match grant/refuse/withdraw/incomplete falls into a new
"Unknown/Needs Review" status instead of silently claiming "Received".
Also wires in AppealDecision (already fetched in county.yaml but never
consulted) so appeal-stage grant/refuse outcomes are captured correctly.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Reject a blank/missing ApplicationNumber instead of coercing it to ""

**Files:**
- Modify: `src/core/normalization/galway_county.py` (the `normalize_county_row` function, currently lines 26-57)
- Test: `tests/unit/pipelines/test_normalize_galway_county.py`
- Modify: `scripts/ingest_galway_county.py:38-51` (the per-record try/except in `run_county_ingestion`) — no behavior change needed here since it already catches `Exception` per-record and counts it as `failed`; confirm this in Step 5, don't add new code unless the test in Step 2 shows otherwise.

**Interfaces:**
- Consumes: nothing new.
- Produces: `normalize_county_row(raw_row, region_config, source_file) -> ApplicationCreate` now raises `ValueError` (message must contain the word `"ApplicationNumber"`) when `raw_row.get("ApplicationNumber")` is missing, `None`, or blank after `_clean_str`, instead of returning an `ApplicationCreate` with `application_ref=""`. Callers (`scripts/ingest_galway_county.py`) already wrap `normalize_county_row` in a `try/except Exception` per-record, so this `ValueError` will be caught there and counted in `failed` automatically — verify this instead of writing new exception-handling code.

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/pipelines/test_normalize_galway_county.py`:

```python
import pytest


def test_normalize_county_row_rejects_missing_application_number():
    raw_row = {
        "OBJECTID": 5,
        "ApplicationNumber": None,
        "ApplicantName": "Test Applicant",
        "ApplicationType": "PERMISSION",
        "ApplicationStatus": "Application Pending",
        "ReceivedDate": "01/01/2020",
        "Decision": "n\\a",
        "Location": "Athenry",
        "Description": "test",
    }
    with pytest.raises(ValueError, match="ApplicationNumber"):
        normalize_county_row(raw_row, region_config=REGION_CONFIG, source_file="arcgis:5")


def test_normalize_county_row_rejects_blank_application_number():
    raw_row = {
        "OBJECTID": 6,
        "ApplicationNumber": "   ",
        "ApplicantName": "Test Applicant",
        "ApplicationType": "PERMISSION",
        "ApplicationStatus": "Application Pending",
        "ReceivedDate": "01/01/2020",
        "Decision": "n\\a",
        "Location": "Athenry",
        "Description": "test",
    }
    with pytest.raises(ValueError, match="ApplicationNumber"):
        normalize_county_row(raw_row, region_config=REGION_CONFIG, source_file="arcgis:6")
```

Add `import pytest` to the top of the file if not already present (check first — the file currently has no imports beyond `from src.core.normalization.galway_county import normalize_county_row`).

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/unit/pipelines/test_normalize_galway_county.py -v -k "rejects"`

Expected: both FAIL — currently `normalize_county_row` returns a value instead of raising, so `pytest.raises` reports `DID NOT RAISE`.

- [ ] **Step 3: Implement the rejection in `normalize_county_row`**

In `src/core/normalization/galway_county.py`, the function currently starts:

```python
def normalize_county_row(raw_row: dict, region_config: dict, source_file: str) -> ApplicationCreate:
    status, event_type = _derive_status(
        raw_row.get("ApplicationStatus"), raw_row.get("Decision"), raw_row.get("AppealDecision")
    )
    description = _clean_str(raw_row.get("Description")) or ""
```

Add the guard immediately after the docstring/signature line, before the `_derive_status` call:

```python
def normalize_county_row(raw_row: dict, region_config: dict, source_file: str) -> ApplicationCreate:
    application_ref = _clean_str(raw_row.get("ApplicationNumber"))
    if not application_ref:
        raise ValueError(
            f"County record missing ApplicationNumber (OBJECTID={raw_row.get('OBJECTID')!r}); "
            "refusing to normalize a row with a blank natural-key component."
        )

    status, event_type = _derive_status(
        raw_row.get("ApplicationStatus"), raw_row.get("Decision"), raw_row.get("AppealDecision")
    )
    description = _clean_str(raw_row.get("Description")) or ""
```

Then update the `ApplicationCreate(...)` construction later in the same function — currently:

```python
        application_ref=_clean_str(raw_row.get("ApplicationNumber")) or "",
```

Change to reuse the already-validated variable:

```python
        application_ref=application_ref,
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/unit/pipelines/test_normalize_galway_county.py -v`

Expected: all 8 tests PASS (6 from Task 1 + 2 new).

- [ ] **Step 5: Confirm the ingestion CLI already handles this exception gracefully**

Read `scripts/ingest_galway_county.py` lines 38-51. Confirm the `try/except Exception` block around the `normalize_county_row(...)` call already exists and increments `failed` on any exception, logging `record OBJECTID=... : {exc}`. This is already the case as of this plan being written — no code change needed here. If for some reason it is not (e.g. this file changed since), add the guard: wrap the `normalize_county_row` call in `try/except ValueError as exc:` that logs and increments `failed`, matching the existing pattern for other exceptions in that loop.

- [ ] **Step 6: Run the full suite**

Run: `source .venv/bin/activate && python -m pytest`

Expected: all tests pass.

- [ ] **Step 7: Update graphify and commit**

```bash
graphify update .
git add src/core/normalization/galway_county.py tests/unit/pipelines/test_normalize_galway_county.py graphify-out/
git commit -m "$(cat <<'EOF'
fix: reject County records with a blank ApplicationNumber

application_ref is half of the (planning_authority, application_ref)
natural key used for upsert dedup in resolve.py. normalize_county_row
previously coerced a missing/blank ApplicationNumber to "", which would
let multiple such records silently collide and overwrite each other
under the same natural key. Now raises ValueError instead, which the
per-record try/except in ingest_galway_county.py already catches and
counts as a failed record rather than silently corrupting data.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Add missing indexes for the columns application_service.search() actually filters and sorts on

**Files:**
- Create: `src/core/db/migrations/versions/0003_add_search_indexes.py`
- Test: `tests/integration/test_migration_applies.py`

**Interfaces:**
- Consumes: nothing new — this task only adds database indexes, no application code changes.
- Produces: after this migration, `applications` has btree indexes on `planning_status_current`, `application_type`, `date_received`, and GIN trigram indexes (via the `pg_trgm` extension) on `applicant_name`, `site_address`, `development_description` — the three columns ORed together in `application_service.search()`'s `q` filter (`src/services/application_service.py:41-50`, unchanged by this task).

- [ ] **Step 1: Write the failing test**

Add to `tests/integration/test_migration_applies.py` (append after the existing two test functions):

```python
def test_applications_has_search_indexes():
    inspector = inspect(engine)
    indexes = inspector.get_indexes("applications")
    index_columns = {tuple(idx["column_names"]) for idx in indexes}

    assert ("planning_status_current",) in index_columns
    assert ("application_type",) in index_columns
    assert ("date_received",) in index_columns


def test_applications_has_trigram_indexes_for_ilike_search():
    # Queries pg_am/pg_opclass system catalogs directly (access method +
    # operator class) instead of pattern-matching the human-readable
    # indexdef string, so this doesn't depend on how a given Postgres
    # version happens to format index DDL text.
    from sqlalchemy import text
    from src.core.db.session import SessionLocal

    session = SessionLocal()
    try:
        result = session.execute(
            text(
                """
                SELECT DISTINCT a.attname AS column_name
                FROM pg_index ix
                JOIN pg_class i ON i.oid = ix.indexrelid
                JOIN pg_class t ON t.oid = ix.indrelid
                JOIN pg_am am ON am.oid = i.relam
                JOIN pg_attribute a
                    ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                JOIN pg_opclass opc ON opc.oid = ix.indclass[0]
                WHERE t.relname = 'applications'
                  AND am.amname = 'gin'
                  AND opc.opcname = 'gin_trgm_ops'
                """
            )
        ).fetchall()
    finally:
        session.close()

    trigram_columns = {row[0] for row in result}
    assert "applicant_name" in trigram_columns
    assert "site_address" in trigram_columns
    assert "development_description" in trigram_columns
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/integration/test_migration_applies.py -v`

Expected: the two new tests FAIL — `test_applications_has_search_indexes` fails because `index_columns` doesn't contain those tuples yet (only the unique-constraint-backed index on `(planning_authority, application_ref)` exists). `test_applications_has_trigram_indexes_for_ilike_search` fails because `index_names` is empty.

- [ ] **Step 3: Write the migration**

Create `src/core/db/migrations/versions/0003_add_search_indexes.py`:

```python
"""add search indexes

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')

    op.create_index(
        'ix_applications_planning_status_current',
        'applications',
        ['planning_status_current'],
    )
    op.create_index(
        'ix_applications_application_type',
        'applications',
        ['application_type'],
    )
    op.create_index(
        'ix_applications_date_received',
        'applications',
        ['date_received'],
    )
    op.create_index(
        'ix_applications_applicant_name_trgm',
        'applications',
        ['applicant_name'],
        postgresql_using='gin',
        postgresql_ops={'applicant_name': 'gin_trgm_ops'},
    )
    op.create_index(
        'ix_applications_site_address_trgm',
        'applications',
        ['site_address'],
        postgresql_using='gin',
        postgresql_ops={'site_address': 'gin_trgm_ops'},
    )
    op.create_index(
        'ix_applications_development_description_trgm',
        'applications',
        ['development_description'],
        postgresql_using='gin',
        postgresql_ops={'development_description': 'gin_trgm_ops'},
    )


def downgrade() -> None:
    op.drop_index('ix_applications_development_description_trgm', table_name='applications')
    op.drop_index('ix_applications_site_address_trgm', table_name='applications')
    op.drop_index('ix_applications_applicant_name_trgm', table_name='applications')
    op.drop_index('ix_applications_date_received', table_name='applications')
    op.drop_index('ix_applications_application_type', table_name='applications')
    op.drop_index('ix_applications_planning_status_current', table_name='applications')
```

- [ ] **Step 4: Apply the migration**

Run: `source .venv/bin/activate && alembic upgrade head`

Expected output ends with something like:
```
INFO  [alembic.runtime.migration] Running upgrade 0002 -> 0003, add search indexes
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/integration/test_migration_applies.py -v`

Expected: all 4 tests PASS (2 pre-existing + 2 new).

- [ ] **Step 6: Run the full suite**

Run: `source .venv/bin/activate && python -m pytest`

Expected: all tests pass.

- [ ] **Step 7: Update graphify and commit**

```bash
graphify update .
git add src/core/db/migrations/versions/0003_add_search_indexes.py tests/integration/test_migration_applies.py graphify-out/
git commit -m "$(cat <<'EOF'
perf: add indexes for the columns application_service.search() filters and sorts on

planning_status_current, application_type, and date_received were
filtered/sorted on with no index; the three ILIKE-searched text columns
(applicant_name, site_address, development_description) had no trigram
support so every keyword in a chat/dashboard q search was a sequential
scan. Fine at today's row count, a landmine once more councils or more
City history is ingested. Adds btree indexes on the first three and
pg_trgm GIN indexes on the text columns.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Post-plan verification (not a task — a checklist for the executing agent to self-check before declaring done)

- [ ] `python -m pytest` passes with 0 failures on the final commit.
- [ ] `alembic current` reports `0003 (head)`.
- [ ] `git log --oneline -3` on `worktree-web-dashboard` shows the three commits from this plan, newest first.
- [ ] `graphify-out/` was updated and committed alongside each code change, not skipped.
