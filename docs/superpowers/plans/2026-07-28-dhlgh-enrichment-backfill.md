# DHLGH Enrichment Backfill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Backfill `applications.site_address` / `applications.site_geometry` from `dhlgh_applications` wherever the matching ladder finds a unique rung-1 or rung-2 match and our own field is currently `NULL`.

**Architecture:** A new script, `scripts/enrich_from_dhlgh.py`, split into a pure planning function (`build_enrichment_plan`, no writes) and an apply function (`apply_enrichment_plan`, does the writes) — mirrors the existing `scripts/validate_dhlgh_matching.py` read-only pattern, but adds a `--apply` flag as an explicit second step. The plan step requires knowing *which* `applications` row matched, which the shipped `ladder.py` doesn't currently expose (`MatchResult` has no candidate identity) — this plan extends `MatchCandidate` with an `application_id` field to close that gap without changing any of the four rungs' matching logic.

**Tech Stack:** Python, SQLAlchemy ORM, Postgres/PostGIS, pytest (existing patterns from `tests/unit/core/test_matching_ladder.py` and `tests/integration/test_validate_dhlgh_matching.py`).

## Global Constraints

- Only rungs 1 and 2 may drive writes; rung 3 and rung 4 matches are never enrichment sources (rung 4 is explicitly manual-review-only per its existing docstring in `ladder.py`).
- Ambiguous results (any rung) are never enrichment sources.
- Only fill fields that are currently `NULL` on the `applications` side — never overwrite a non-null `site_address` or `site_geometry`.
- No change to weekly ingestion pipeline (`com.planning-intelligence.weekly-ingestion.plist`) — this stays a manually-invoked script.
- No change to rung 1-4 matching logic/thresholds — only additive (an id field).

---

### Task 1: Add `application_id` to `MatchCandidate`

**Files:**
- Modify: `src/core/matching/ladder.py:37-40` (the `MatchCandidate` NamedTuple)
- Modify: `scripts/validate_dhlgh_matching.py:49-56` (the one place `MatchCandidate` is constructed today)
- Test: `tests/unit/core/test_matching_ladder.py` (add one test; existing tests must keep passing after being updated to supply the new required field)

**Interfaces:**
- Consumes: nothing new.
- Produces: `MatchCandidate(application_ref: str, site_address: str | None, site_geometry_wkt: str | None, application_id: uuid.UUID)` — Task 2 relies on this field to look up which `applications` row to enrich.

This is a required-field addition to an existing NamedTuple, so every existing call site and every existing test that constructs a `MatchCandidate` needs a fourth value. There is no matching logic change — rungs 1-4 never read `application_id`, they only ever return `MatchResult`.

- [ ] **Step 1: Update the `MatchCandidate` definition**

In `src/core/matching/ladder.py`, change:

```python
class MatchCandidate(NamedTuple):
    application_ref: str
    site_address: str | None
    site_geometry_wkt: str | None
```

to:

```python
class MatchCandidate(NamedTuple):
    application_ref: str
    site_address: str | None
    site_geometry_wkt: str | None
    application_id: uuid.UUID
```

Add `import uuid` at the top of the file alongside the existing imports.

- [ ] **Step 2: Run the existing ladder test suite to see it fail**

Run: `uv run pytest tests/unit/core/test_matching_ladder.py -v`
Expected: multiple FAIL / ERROR — `MatchCandidate() missing 1 required positional argument: 'application_id'` — because every existing test constructs `MatchCandidate` with only 3 positional args.

- [ ] **Step 3: Fix every existing `MatchCandidate(...)` call site in the test file**

Open `tests/unit/core/test_matching_ladder.py`. For every `MatchCandidate(application_ref=..., site_address=..., site_geometry_wkt=...)` call, add `application_id=uuid.uuid4()` (the tests never assert on this value — they only test rung logic, which ignores it — so any unique UUID per candidate is fine). The file already imports `uuid` at the top (`import uuid`), so no new import is needed there.

- [ ] **Step 4: Fix the one production call site**

In `scripts/validate_dhlgh_matching.py`, change:

```python
candidates = [
    MatchCandidate(
        application_ref=row.application_ref,
        site_address=row.site_address,
        site_geometry_wkt=None,
    )
    for row in our_rows
]
```

to:

```python
candidates = [
    MatchCandidate(
        application_ref=row.application_ref,
        site_address=row.site_address,
        site_geometry_wkt=None,
        application_id=row.id,
    )
    for row in our_rows
]
```

- [ ] **Step 5: Run the full ladder unit suite and the validation integration test to confirm nothing regressed**

Run: `uv run pytest tests/unit/core/test_matching_ladder.py tests/integration/test_validate_dhlgh_matching.py -v`
Expected: all PASS (this requires Postgres running — the integration test hits the real DB; if it fails to connect, start the DB container before continuing).

- [ ] **Step 6: Write a new test confirming `application_id` round-trips through rung 1**

Add to `tests/unit/core/test_matching_ladder.py`:

```python
def test_rung1_match_candidate_carries_application_id_for_caller_lookup():
    target_id = uuid.uuid4()
    candidates = [
        MatchCandidate(application_ref="17792", site_address="Cahernamona ,", site_geometry_wkt=None, application_id=target_id),
        MatchCandidate(application_ref="20651", site_address="Ardgaineen , Claregalway", site_geometry_wkt=None, application_id=uuid.uuid4()),
    ]
    result = rung1_ref_match("17792", "Galway County Council", candidates)
    assert result.matched is True
    # rung1_ref_match itself doesn't return the id (MatchResult is unchanged) —
    # this test documents that the caller must re-filter candidates by the
    # same predicate to recover which one matched, which Task 2 does.
    matches = [c for c in candidates if c.application_ref == "17792"]
    assert len(matches) == 1
    assert matches[0].application_id == target_id
```

- [ ] **Step 7: Run the new test**

Run: `uv run pytest tests/unit/core/test_matching_ladder.py -v -k application_id`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/core/matching/ladder.py scripts/validate_dhlgh_matching.py tests/unit/core/test_matching_ladder.py
git commit -m "feat: add application_id to MatchCandidate for enrichment lookups"
```

---

### Task 2: `build_enrichment_plan` (read-only planning function)

**Files:**
- Create: `scripts/enrich_from_dhlgh.py`
- Test: `tests/unit/core/test_enrich_from_dhlgh.py`

**Interfaces:**
- Consumes: `run_ladder`, `MatchCandidate` from `src.core.matching.ladder` (Task 1's signature); `Application`, `DHLGHApplication` models; `AUTHORITIES` list (copy the same `["Galway City Council", "Galway County Council"]` constant used in `scripts/validate_dhlgh_matching.py` — do not import it, since it's a module-level constant not exported for reuse; duplicating a 2-item list is simpler than adding cross-script coupling).
- Produces: `build_enrichment_plan(session: Session, authority_filter: str | None = None) -> list[dict]`. Each dict has keys: `application_id: uuid.UUID`, `field: str` (`"site_address"` or `"site_geometry"`), `new_value: str` (for `site_address`) or the WKT string (for `site_geometry`), `application_ref: str` (our side's ref, for dry-run display), `source_dhlgh_ref: str`, `rung: int` (1 or 2). Task 3's `apply_enrichment_plan` consumes exactly this shape.

Because `run_ladder`'s `MatchResult` doesn't carry which candidate matched (only `matched`/`rung`/`ambiguous`), and rungs 1/2 are pure functions over the `candidates` list, the planner recovers the matched candidate by re-applying the same equality predicate the rung itself used, now that `application_id` (Task 1) is available on `MatchCandidate` to identify it.

- [ ] **Step 1: Write the failing unit tests**

Create `tests/unit/core/test_enrich_from_dhlgh.py`:

```python
import uuid
from unittest.mock import MagicMock

from scripts.enrich_from_dhlgh import build_enrichment_plan


def _make_session_with_rows(app_rows, dhlgh_rows):
    session = MagicMock()

    def scalars_side_effect(query):
        query_str = str(query)
        result = MagicMock()
        if "dhlgh_applications" in query_str:
            result.all.return_value = dhlgh_rows
        else:
            result.all.return_value = app_rows
        return result

    session.scalars.side_effect = scalars_side_effect
    return session


class FakeApplication:
    def __init__(self, id, application_ref, site_address, site_geometry, planning_authority):
        self.id = id
        self.application_ref = application_ref
        self.site_address = site_address
        self.site_geometry = site_geometry
        self.planning_authority = planning_authority


class FakeDHLGH:
    def __init__(self, application_ref, site_address, site_geometry, planning_authority):
        self.application_ref = application_ref
        self.site_address = site_address
        self.site_geometry = site_geometry
        self.planning_authority = planning_authority


def test_rung1_match_with_null_site_address_produces_planned_update():
    app_id = uuid.uuid4()
    app = FakeApplication(app_id, "17792", None, None, "Galway County Council")
    dhlgh = FakeDHLGH("17792", "Cahernamona, Co. Galway", None, "Galway County Council")

    session = _make_session_with_rows([app], [dhlgh])
    plan = build_enrichment_plan(session, authority_filter="Galway County Council")

    assert len(plan) == 1
    assert plan[0]["application_id"] == app_id
    assert plan[0]["field"] == "site_address"
    assert plan[0]["new_value"] == "Cahernamona, Co. Galway"
    assert plan[0]["rung"] == 1


def test_match_with_non_null_site_address_produces_no_planned_update_for_that_field():
    app_id = uuid.uuid4()
    app = FakeApplication(app_id, "17792", "Already has an address", None, "Galway County Council")
    dhlgh = FakeDHLGH("17792", "Cahernamona, Co. Galway", None, "Galway County Council")

    session = _make_session_with_rows([app], [dhlgh])
    plan = build_enrichment_plan(session, authority_filter="Galway County Council")

    assert plan == []


def test_no_match_produces_no_planned_update():
    app = FakeApplication(uuid.uuid4(), "17792", None, None, "Galway County Council")
    dhlgh = FakeDHLGH("99999", "Unrelated address", None, "Galway County Council")

    session = _make_session_with_rows([app], [dhlgh])
    plan = build_enrichment_plan(session, authority_filter="Galway County Council")

    assert plan == []


def test_ambiguous_match_produces_no_planned_update():
    app1 = FakeApplication(uuid.uuid4(), "17792", None, None, "Galway County Council")
    app2 = FakeApplication(uuid.uuid4(), "17792", None, None, "Galway County Council")
    dhlgh = FakeDHLGH("17792", "Cahernamona, Co. Galway", None, "Galway County Council")

    session = _make_session_with_rows([app1, app2], [dhlgh])
    plan = build_enrichment_plan(session, authority_filter="Galway County Council")

    assert plan == []
```

Note: these unit tests use `MagicMock` for the session rather than real Postgres because `build_enrichment_plan`'s rung-1/2-only logic path never actually calls rung 3/4 (which need a real DB session for PostGIS/trigram queries) as long as rung 1 or rung 2 resolves first — but to keep the unit tests fully DB-free and fast, this task's tests only exercise cases that resolve at rung 1. Rung 3/4 exclusion and the geometry-field case are covered by the Task 2 integration test in Step 6 below, which needs real Postgres.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/core/test_enrich_from_dhlgh.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.enrich_from_dhlgh'` (or ImportError for `build_enrichment_plan`).

- [ ] **Step 3: Write the implementation**

Create `scripts/enrich_from_dhlgh.py`:

```python
"""
DHLGH enrichment backfill (spec
docs/superpowers/specs/2026-07-28-dhlgh-enrichment-backfill-design.md).
Backfills applications.site_address / site_geometry from
dhlgh_applications wherever the matching ladder (src/core/matching/ladder.py)
finds a unique rung-1 or rung-2 match and our own field is currently NULL.

build_enrichment_plan performs no writes. apply_enrichment_plan performs
the writes and must only be called after reviewing the plan (see --apply
flag below).
"""

import argparse
import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.core.db.session import SessionLocal
from src.core.matching.ladder import MatchCandidate, run_ladder
from src.core.models.application import Application
from src.core.models.dhlgh_application import DHLGHApplication

logger = logging.getLogger(__name__)

AUTHORITIES = ["Galway City Council", "Galway County Council"]


def build_enrichment_plan(session: Session, authority_filter: str | None = None) -> list[dict]:
    authorities = [authority_filter] if authority_filter else AUTHORITIES

    plan: list[dict] = []

    for authority in authorities:
        app_query = select(Application).where(Application.planning_authority == authority)
        dhlgh_query = select(DHLGHApplication).where(DHLGHApplication.planning_authority == authority)

        our_rows = session.scalars(app_query).all()
        dhlgh_rows = session.scalars(dhlgh_query).all()

        candidates = [
            MatchCandidate(
                application_ref=row.application_ref,
                site_address=row.site_address,
                site_geometry_wkt=None,
                application_id=row.id,
            )
            for row in our_rows
        ]
        by_id = {row.id: row for row in our_rows}

        for dhlgh_row in dhlgh_rows:
            geom_wkt = (
                session.scalar(select(func.ST_AsText(dhlgh_row.site_geometry)))
                if dhlgh_row.site_geometry is not None
                else None
            )
            result = run_ladder(
                session,
                dhlgh_ref=dhlgh_row.application_ref,
                dhlgh_address=dhlgh_row.site_address,
                dhlgh_geom_wkt=geom_wkt,
                authority=authority,
                candidates=candidates,
            )

            if not result.matched or result.rung not in (1, 2):
                continue

            matched_candidate = _find_matched_candidate(result.rung, dhlgh_row, candidates)
            if matched_candidate is None:
                continue

            app_row = by_id[matched_candidate.application_id]

            if app_row.site_address is None and dhlgh_row.site_address:
                plan.append({
                    "application_id": app_row.id,
                    "application_ref": app_row.application_ref,
                    "field": "site_address",
                    "new_value": dhlgh_row.site_address,
                    "source_dhlgh_ref": dhlgh_row.application_ref,
                    "rung": result.rung,
                })

            if app_row.site_geometry is None and dhlgh_row.site_geometry is not None:
                dhlgh_geom_wkt = session.scalar(select(func.ST_AsText(dhlgh_row.site_geometry)))
                plan.append({
                    "application_id": app_row.id,
                    "application_ref": app_row.application_ref,
                    "field": "site_geometry",
                    "new_value": dhlgh_geom_wkt,
                    "source_dhlgh_ref": dhlgh_row.application_ref,
                    "rung": result.rung,
                })

    return plan


def _find_matched_candidate(rung: int, dhlgh_row, candidates: list[MatchCandidate]) -> MatchCandidate | None:
    """Re-applies the same equality predicate the winning rung used, to
    recover which candidate it was (run_ladder's MatchResult only reports
    matched/rung/ambiguous, not candidate identity)."""
    if rung == 1:
        from src.core.normalization.application_ref import normalize_application_ref
        normalized = normalize_application_ref(dhlgh_row.application_ref, dhlgh_row.planning_authority)
        target = normalized if normalized is not None else dhlgh_row.application_ref
        hits = [c for c in candidates if c.application_ref == target]
    elif rung == 2:
        from src.core.normalization.address import normalize_address
        target = normalize_address(dhlgh_row.site_address)
        hits = [
            c for c in candidates
            if c.site_address and normalize_address(c.site_address) == target
        ]
    else:
        return None

    return hits[0] if len(hits) == 1 else None


def apply_enrichment_plan(session: Session, plan: list[dict]) -> int:
    updated = 0
    for item in plan:
        app_row = session.get(Application, item["application_id"])
        setattr(app_row, item["field"], item["new_value"])
        updated += 1
    session.commit()
    return updated


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Apply the plan (default is dry-run print only)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    session = SessionLocal()
    try:
        plan = build_enrichment_plan(session)
        by_field = {}
        by_rung = {}
        for item in plan:
            by_field[item["field"]] = by_field.get(item["field"], 0) + 1
            by_rung[item["rung"]] = by_rung.get(item["rung"], 0) + 1

        logger.info("Enrichment plan: %d planned updates. By field: %s. By rung: %s", len(plan), by_field, by_rung)
        for item in plan[:10]:
            print(item)

        if args.apply:
            updated = apply_enrichment_plan(session, plan)
            logger.info("Applied %d updates.", updated)
        else:
            logger.info("Dry-run only (no writes). Re-run with --apply to write these changes.")
    finally:
        session.close()
```

- [ ] **Step 4: Run the unit tests to verify they pass**

Run: `uv run pytest tests/unit/core/test_enrich_from_dhlgh.py -v`
Expected: all 4 PASS

- [ ] **Step 5: Run the full unit suite to check for regressions**

Run: `uv run pytest tests/unit/ -v`
Expected: all PASS

- [ ] **Step 6: Write and run an integration test covering rung 3/4 exclusion and the geometry field (needs real Postgres)**

Create `tests/integration/test_enrich_from_dhlgh.py`:

```python
import uuid

import sqlalchemy as sa

from scripts.enrich_from_dhlgh import build_enrichment_plan
from src.core.db.session import SessionLocal
from src.core.models.application import Application
from src.core.models.dhlgh_application import DHLGHApplication


def _cleanup(session):
    session.execute(sa.text("DELETE FROM applications WHERE application_ref LIKE 'ENRICHTEST/%'"))
    session.execute(sa.text("DELETE FROM dhlgh_applications WHERE application_ref LIKE 'ENRICHTEST/%'"))
    session.commit()


def _base_application_kwargs(**overrides):
    kwargs = dict(
        id=uuid.uuid4(),
        planning_authority="Galway County Council",
        source_entity="GALWAY_COUNTY",
        application_ref="ENRICHTEST/001",
        applicant_name="Test",
        site_address=None,
        development_description="Test",
        application_type="Permission",
        planning_status_current="Received",
        date_received="2026-01-01",
        source_system="test",
        source_file="test",
    )
    kwargs.update(overrides)
    return kwargs


def _base_dhlgh_kwargs(**overrides):
    kwargs = dict(
        id=uuid.uuid4(),
        planning_authority="Galway County Council",
        source_entity="DHLGH_NATIONAL",
        application_ref="ENRICHTEST/001",
        development_description="Test",
        site_address="Test address one",
        planning_status_current="Received",
        date_received="2026-01-01",
        source_system="test",
    )
    kwargs.update(overrides)
    return kwargs


def test_rung1_match_plans_site_address_backfill_only_when_null():
    session = SessionLocal()
    try:
        _cleanup(session)
        session.add(Application(**_base_application_kwargs()))
        session.add(DHLGHApplication(**_base_dhlgh_kwargs()))
        session.commit()

        plan = build_enrichment_plan(session, authority_filter="Galway County Council")
        matching = [p for p in plan if p["application_ref"] == "ENRICHTEST/001"]

        assert len(matching) == 1
        assert matching[0]["field"] == "site_address"
        assert matching[0]["new_value"] == "Test address one"
        assert matching[0]["rung"] == 1
    finally:
        _cleanup(session)
        session.close()


def test_no_plan_when_our_site_address_already_non_null():
    session = SessionLocal()
    try:
        _cleanup(session)
        session.add(Application(**_base_application_kwargs(site_address="Already populated")))
        session.add(DHLGHApplication(**_base_dhlgh_kwargs()))
        session.commit()

        plan = build_enrichment_plan(session, authority_filter="Galway County Council")
        matching = [p for p in plan if p["application_ref"] == "ENRICHTEST/001"]

        assert matching == []
    finally:
        _cleanup(session)
        session.close()
```

- [ ] **Step 7: Run the integration tests**

Run: `uv run pytest tests/integration/test_enrich_from_dhlgh.py -v`
Expected: both PASS (requires Postgres container running — start it first if `OperationalError` occurs).

- [ ] **Step 8: Run the full test suite (unit + integration) to confirm no regressions anywhere**

Run: `uv run pytest -v`
Expected: all PASS, count should be the prior full-suite count (166, per the progress ledger) plus the 4 new unit tests plus the 2 new integration tests.

- [ ] **Step 9: Commit**

```bash
git add scripts/enrich_from_dhlgh.py tests/unit/core/test_enrich_from_dhlgh.py tests/integration/test_enrich_from_dhlgh.py
git commit -m "feat: add build_enrichment_plan for DHLGH backfill (read-only)"
```

---

### Task 3: `apply_enrichment_plan` + CLI wiring, integration test for writes

**Files:**
- Modify: `scripts/enrich_from_dhlgh.py` (already contains `apply_enrichment_plan` and the `--apply` CLI flag from Task 2's Step 3 — this task adds test coverage proving the write behavior is correct and safe)
- Test: `tests/integration/test_enrich_from_dhlgh.py` (add to the file created in Task 2)

**Interfaces:**
- Consumes: `apply_enrichment_plan(session: Session, plan: list[dict]) -> int` (already implemented in Task 2, Step 3).
- Produces: nothing new for other tasks — this is the final implementation task before manual functional testing.

`apply_enrichment_plan` was written in Task 2 alongside `build_enrichment_plan` since they live in the same small file, but its correctness (only touches planned fields, never touches unrelated columns, never touches non-null fields) has not yet been tested against a real Postgres row. This task closes that gap.

- [ ] **Step 1: Write the failing integration test**

Add to `tests/integration/test_enrich_from_dhlgh.py`:

```python
def test_apply_enrichment_plan_only_changes_planned_fields():
    session = SessionLocal()
    try:
        _cleanup(session)
        app = Application(**_base_application_kwargs(site_address=None))
        session.add(app)
        session.add(DHLGHApplication(**_base_dhlgh_kwargs(site_address="Backfilled address")))
        session.commit()

        original_ref = app.application_ref
        original_applicant = app.applicant_name
        original_status = app.planning_status_current

        plan = build_enrichment_plan(session, authority_filter="Galway County Council")
        matching_plan = [p for p in plan if p["application_ref"] == "ENRICHTEST/001"]
        assert len(matching_plan) == 1

        from scripts.enrich_from_dhlgh import apply_enrichment_plan
        updated_count = apply_enrichment_plan(session, matching_plan)

        session.expire_all()
        refreshed = session.get(Application, app.id)

        assert updated_count == 1
        assert refreshed.site_address == "Backfilled address"
        # Unrelated fields must be untouched.
        assert refreshed.application_ref == original_ref
        assert refreshed.applicant_name == original_applicant
        assert refreshed.planning_status_current == original_status
    finally:
        _cleanup(session)
        session.close()


def test_apply_enrichment_plan_with_empty_plan_does_nothing():
    session = SessionLocal()
    try:
        _cleanup(session)
        from scripts.enrich_from_dhlgh import apply_enrichment_plan
        updated_count = apply_enrichment_plan(session, [])
        assert updated_count == 0
    finally:
        _cleanup(session)
        session.close()
```

- [ ] **Step 2: Run to verify they fail (or pass immediately if the implementation is already correct)**

Run: `uv run pytest tests/integration/test_enrich_from_dhlgh.py -v -k apply_enrichment_plan`
Expected: since `apply_enrichment_plan` was already written in Task 2, this may PASS immediately. If it fails, inspect the failure — the most likely cause is `session.get` returning a stale cached object rather than the committed row; if so, add `session.expire_all()` before the `session.get(Application, item["application_id"])` call inside `apply_enrichment_plan` in `scripts/enrich_from_dhlgh.py`.

- [ ] **Step 3: Confirm passing**

Run: `uv run pytest tests/integration/test_enrich_from_dhlgh.py -v`
Expected: all 4 tests in the file PASS (2 from Task 2, 2 new).

- [ ] **Step 4: Run the full test suite one more time**

Run: `uv run pytest -v`
Expected: all PASS, no regressions.

- [ ] **Step 5: Update graphify**

Run: `graphify update .`
This is an AST-only, no-API-cost update per this project's CLAUDE.md — run it and include `graphify-out/` changes in the commit below.

- [ ] **Step 6: Commit**

```bash
git add scripts/enrich_from_dhlgh.py tests/integration/test_enrich_from_dhlgh.py graphify-out/
git commit -m "test: verify apply_enrichment_plan only writes planned fields"
```

---

### Task 4: Live dry-run, live apply, and manual functional verification

**Files:** none created or modified — this task runs the script against the live database and manually verifies results through the chat UI. No code changes are expected; if the dry-run output looks implausible, stop and report back rather than guessing a fix.

**Interfaces:**
- Consumes: `scripts/enrich_from_dhlgh.py` CLI (Tasks 2-3).
- Produces: enriched rows in the live `applications` table; no interface for further tasks (this is the last task in the plan).

- [ ] **Step 1: Confirm Postgres is running and the full suite is green immediately before the live run**

Run: `uv run pytest -v`
Expected: all PASS. If Postgres is down, start the container first.

- [ ] **Step 2: Run the dry-run against the live DB**

Run: `uv run python scripts/enrich_from_dhlgh.py`
Expected: log line `Enrichment plan: N planned updates. By field: {...}. By rung: {...}`, plus up to 10 example planned-update dicts printed. Review the counts for plausibility — they should be well below the validation pass's rung 1+2 totals (14,880 + 1,574 = 16,454 DHLGH-side matches per the Task 7 validation results in the DHLGH spec section 11), since many of those already have non-null `site_address` on our side and won't need backfilling.

- [ ] **Step 3: Apply the plan**

Run: `uv run python scripts/enrich_from_dhlgh.py --apply`
Expected: log line `Applied N updates.` where N matches the dry-run's planned-update count from Step 2.

- [ ] **Step 4: Spot-check one rung-1 enriched row directly in the DB**

Pick one `application_ref` from the Step 2 example output where `rung == 1`. Run:

```bash
uv run python -c "
from src.core.db.session import SessionLocal
from src.core.models.application import Application
session = SessionLocal()
row = session.query(Application).filter_by(application_ref='<REF_FROM_STEP_2>').first()
print(row.application_ref, row.site_address, row.site_geometry)
"
```

Expected: `site_address` is now populated (or `site_geometry` is, depending on which field was planned) and matches the DHLGH source value shown in the Step 2 output for that ref.

- [ ] **Step 5: Spot-check one rung-2 enriched row the same way**

Repeat Step 4 for an example row where `rung == 2`.

- [ ] **Step 6: Start the chat UI and confirm enriched data surfaces**

Follow this project's existing run instructions for `chat.html` / `chat_service.py` (check `README.md` or existing scripts if unsure of the exact command). Ask a question referencing the address of one of the rows enriched in Step 4 or 5 (e.g. "what's happening at <the address>"), and confirm the chat response reflects the newly-populated address — this is the first time DHLGH-sourced data is visible through the actual application, closing the gap identified at the end of the matching-ladder plan.

- [ ] **Step 7: Record results**

Append a short "Results" section to this plan file (`docs/superpowers/plans/2026-07-28-dhlgh-enrichment-backfill.md`) noting: total updates applied, breakdown by field/rung, and confirmation that the chat UI spot-check succeeded (or what was found if it didn't). Commit this update.

```bash
git add docs/superpowers/plans/2026-07-28-dhlgh-enrichment-backfill.md
git commit -m "docs: record DHLGH enrichment backfill live run results"
```

---

## Results

**First live run (buggy, later rolled back):** applied 16,454 updates. Manual
spot-check of `application_ref='23/60037'` found its stored `site_geometry`
did not match the DHLGH source it was sampled against. Root cause: 11
distinct DHLGH rows shared the same normalized address as this application,
each independently resolving at rung 2, and `apply_enrichment_plan`'s
list-order application let the last one silently win. All 16,393 affected
rows were rolled back to `NULL` (confirmed via `src/pipelines/resolve.py`
that no other code path writes `applications.site_geometry`, so the blanket
reset was exact). Fixed by adding `_drop_conflicting_targets` to
`build_enrichment_plan` (commit `c925c6b`): any `(application_id, field)`
target with more than one competing plan entry is dropped entirely rather
than letting apply order pick a winner.

**Second live run (with the fix), against the same ~39k-row Galway dataset:**

- Dry-run planned **16,370 updates**, all for `site_geometry` (none for
  `site_address`, since address coverage was already largely populated).
  By rung: **14,871 at rung 1**, **1,499 at rung 2**.
- `_drop_conflicting_targets` dropped **84 planned updates across 23
  `(application_id, field)` targets** with conflicting DHLGH sources —
  exactly the class of bug found in the first run, now caught before any
  write. This is 84 fewer planned updates than the pre-fix run
  (16,454 → 16,370), matching the logged drop count precisely.
- Applied: **16,370 updates** (log: `Applied 16370 updates.`).

**Spot-checks after the fix:**

- Rung-1 sample `23/60044`: confirmed enriched `site_geometry` matches its
  DHLGH source (`2360044`) after accounting for `normalize_application_ref`
  normalization (`23/60044` → `2360044`).
- Rung-2 samples `23/119` (`<-> DHLGH 23119`) and `25/6` (`<-> DHLGH 256`):
  both confirmed clean — unique on both sides of the match, no competing
  DHLGH row targeting the same `(application_id, field)`, geometry matches
  source. One earlier rung-2 candidate (`25/60107`) was found to still have
  a second, independent DHLGH row (`2560107`) resolving to the same
  application at rung 1 — correctly caught and dropped by
  `_drop_conflicting_targets`, confirming the fix's collision handling
  extends beyond the original bug scenario.

**UI verification:** started the app (`uv run uvicorn src.web.main:app
--port 8010`) with Ollama running. Chat endpoint (`POST /chat`) correctly
parsed a natural-language query for `23/119` and returned a matching
results table. The application detail page
(`/applications/Galway%20City%20Council/23/119`) renders the enriched
`site_address` field. The detail page has no map/geometry rendering path in
its template (no `map`/`leaflet`/`lat`/`lon`/`geojson` markup), so
`site_geometry` enrichment is verified at the DB level only
(`rung2check.log`), consistent with the rest of the UI never surfacing raw
geometry.
```
