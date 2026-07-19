# DHLGH Cross-Source Identity Matching Ladder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the 4-rung deterministic matching ladder from spec section 9 (`docs/superpowers/specs/2026-07-10-dhlgh-national-source-design.md`) and a validation-pass CLI that runs it across the full Galway overlap between `applications` (527 City + 20,375 County rows) and `dhlgh_applications` (3,401 City + 18,674 County rows, already live-ingested), reporting per-rung match counts and the trial-period exit-criteria stats.

**Architecture:** Each rung is a pure function: given one `DHLGHApplication` row and a list of candidate `Application` rows already filtered to the same `planning_authority`, return zero, one, or "ambiguous" (>1 candidate). The ladder function tries rungs in order, stopping at the first rung that returns a unique match, and logs which rung resolved each match (or that none did). The validation-pass CLI loads all rows from both tables into memory (won't exceed ~24k+21k rows, small enough for a single process), groups `Application` rows by `planning_authority` once, then iterates `dhlgh_applications` rows through the ladder and tallies results into a report — **no writes to `applications`, ever**.

**Tech Stack:** Python 3.11, SQLAlchemy 2.0 ORM, PostgreSQL + PostGIS (`geoalchemy2`, `ST_Distance`/`ST_DWithin` for rung 3), existing `gin_trgm_ops` indexes + PostgreSQL `similarity()` function (`pg_trgm` extension, already installed per migration 0003) for rung 4, pytest.

## Global Constraints

- **No merge, no write to `applications` table.** This pass only computes and reports match statistics (spec section 9: "does not implement... or run the validation pass" refers to prior work; this plan is exactly that follow-up, and it is explicitly read-only against `applications`).
- A rung that finds **more than one** candidate is treated as **no match** for that rung, not a match — log it as ambiguous and fall through to the next rung.
- Rung 1 and rung 2 must reuse the existing tested helpers verbatim: `normalize_application_ref(application_number: str, authority: str) -> str | None` (`src/core/normalization/application_ref.py`) and `normalize_address(address: str) -> str` (`src/core/normalization/address.py`). Do not reimplement or modify their logic.
- Rung 2 comparison is **exact string equality** after normalization — never fuzzy. Fuzzy matching is rung 4 only.
- All ladder unit tests must use realistic authority/ref/address/geometry combinations grounded in the real values already confirmed live in the DB during planning (see fixtures embedded in each task below) — not invented placeholder strings.
- `planning_authority` values are the literal strings `"Galway City Council"` and `"Galway County Council"` in both tables (confirmed identical spelling via direct query) — every rung's candidate-filtering step must include an authority match, per spec.
- `applications.site_geometry` is currently 0% populated (0 of 20,902 rows) — rung 3 is expected to match **zero** rows in the current dataset. This is a known, correct outcome to report, not a bug to work around.

---

## File Structure

- `src/core/matching/ladder.py` — the four rung functions plus the orchestrating `run_ladder()` function. New module; matching logic doesn't belong in `normalization/` (which is source-row → schema normalization) or `pipelines/` (which is ingest orchestration).
- `src/core/matching/__init__.py` — empty, makes it a package.
- `scripts/validate_dhlgh_matching.py` — CLI entrypoint for the validation pass. Follows the existing `scripts/ingest_dhlgh.py` pattern (own `SessionLocal()`, `argparse`, prints a summary dict).
- `tests/unit/core/test_matching_ladder.py` — unit tests per rung, using in-memory `Application`/`DHLGHApplication`-shaped plain objects (no DB) via light stub classes, since each rung function takes plain field values, not ORM objects (see Task 1 interface).
- `tests/integration/test_validate_dhlgh_matching.py` — integration test seeding real rows into both tables via `SessionLocal()`, running the full validation pass, and asserting on the report's rung-by-rung counts.

---

### Task 1: Rung 1 — exact ref match function

**Files:**
- Create: `src/core/matching/__init__.py`
- Create: `src/core/matching/ladder.py`
- Test: `tests/unit/core/test_matching_ladder.py`

**Interfaces:**
- Consumes: `normalize_application_ref(application_number: str, authority: str) -> str | None` from `src/core/normalization/application_ref.py`.
- Produces: `MatchCandidate` (a `NamedTuple` with fields `application_ref: str`, `site_address: str | None`, `site_geometry_wkt: str | None`) — the plain-value shape every rung function and the CLI will pass around, decoupled from ORM row objects. Also produces `MatchResult` (`NamedTuple` with `matched: bool`, `rung: int | None`, `ambiguous: bool`) and `rung1_ref_match(dhlgh_ref: str, authority: str, candidates: list[MatchCandidate]) -> MatchResult`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/core/test_matching_ladder.py
from src.core.matching.ladder import MatchCandidate, rung1_ref_match


def test_rung1_matches_unique_exact_county_ref():
    # Real confirmed match pulled live from the DB during planning:
    # applications and dhlgh_applications both have planning_authority
    # "Galway County Council", application_ref "17792".
    candidates = [
        MatchCandidate(application_ref="17792", site_address="Cahernamona ,", site_geometry_wkt=None),
        MatchCandidate(application_ref="20651", site_address="Ardgaineen , Claregalway", site_geometry_wkt=None),
    ]
    result = rung1_ref_match("17792", "Galway County Council", candidates)
    assert result.matched is True
    assert result.rung == 1
    assert result.ambiguous is False


def test_rung1_no_match_when_ref_absent():
    candidates = [
        MatchCandidate(application_ref="20651", site_address="Ardgaineen , Claregalway", site_geometry_wkt=None),
    ]
    result = rung1_ref_match("99999", "Galway County Council", candidates)
    assert result.matched is False
    assert result.ambiguous is False


def test_rung1_ambiguous_when_ref_appears_twice():
    # Duplicate refs would only occur if the natural-key constraint were
    # ever bypassed — the ladder must not assume it can't happen and must
    # treat >1 candidate as ambiguous, not as a match.
    candidates = [
        MatchCandidate(application_ref="17792", site_address="Cahernamona ,", site_geometry_wkt=None),
        MatchCandidate(application_ref="17792", site_address="Duplicate entry", site_geometry_wkt=None),
    ]
    result = rung1_ref_match("17792", "Galway County Council", candidates)
    assert result.matched is False
    assert result.ambiguous is True


def test_rung1_normalizes_city_dhlgh_ref_before_comparing():
    # Real City case confirmed live: DHLGH's raw "2660243" for Galway City
    # Council normalizes (via normalize_application_ref) to "26/60243",
    # which is the shape our own applications.application_ref already uses
    # (confirmed: 525/527 City refs match ^\d{2}/\d+$).
    candidates = [
        MatchCandidate(application_ref="26/60243", site_address="7 Lower Canal Road, Galway", site_geometry_wkt=None),
    ]
    result = rung1_ref_match("2660243", "Galway City Council", candidates)
    assert result.matched is True
    assert result.rung == 1


def test_rung1_no_match_when_ref_cannot_normalize_and_no_raw_equal():
    # Real County case: normalize_application_ref("2661119", "Galway County
    # Council") returns None (documented ambiguous shape, spec section
    # 9.1). Rung 1 must fall back to comparing the raw string as-is, and
    # here it also has no equal candidate, so it's a clean no-match, not
    # an error.
    candidates = [
        MatchCandidate(application_ref="26170", site_address="", site_geometry_wkt=None),
    ]
    result = rung1_ref_match("2661119", "Galway County Council", candidates)
    assert result.matched is False
    assert result.ambiguous is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/core/test_matching_ladder.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.core.matching'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/core/matching/__init__.py
```

```python
# src/core/matching/ladder.py
"""
Cross-source identity matching ladder (spec section 9,
docs/superpowers/specs/2026-07-10-dhlgh-national-source-design.md). Given
a DHLGH row and the subset of our own `applications` rows sharing its
planning_authority, tries each rung in order and stops at the first rung
that finds a UNIQUE match. A rung returning more than one candidate is
ambiguous, not a match, and the caller falls through to the next rung.

This module does not touch the database or write to `applications` — it
operates on plain MatchCandidate values so it stays trivially unit
testable. Callers (the validation-pass CLI) are responsible for loading
candidates and persisting/reporting results.
"""

from typing import NamedTuple

from src.core.normalization.application_ref import normalize_application_ref


class MatchCandidate(NamedTuple):
    application_ref: str
    site_address: str | None
    site_geometry_wkt: str | None


class MatchResult(NamedTuple):
    matched: bool
    rung: int | None
    ambiguous: bool


def rung1_ref_match(
    dhlgh_ref: str, authority: str, candidates: list[MatchCandidate]
) -> MatchResult:
    normalized = normalize_application_ref(dhlgh_ref, authority)
    target = normalized if normalized is not None else dhlgh_ref

    hits = [c for c in candidates if c.application_ref == target]

    if len(hits) == 1:
        return MatchResult(matched=True, rung=1, ambiguous=False)
    if len(hits) > 1:
        return MatchResult(matched=False, rung=None, ambiguous=True)
    return MatchResult(matched=False, rung=None, ambiguous=False)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/core/test_matching_ladder.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add src/core/matching/__init__.py src/core/matching/ladder.py tests/unit/core/test_matching_ladder.py
git commit -m "feat: add rung 1 (exact application_ref) matching function"
```

---

### Task 2: Rung 2 — normalized address match function

**Files:**
- Modify: `src/core/matching/ladder.py`
- Modify: `tests/unit/core/test_matching_ladder.py`

**Interfaces:**
- Consumes: `normalize_address(address: str) -> str` from `src/core/normalization/address.py`; `MatchCandidate`, `MatchResult` from Task 1.
- Produces: `rung2_address_match(dhlgh_address: str | None, candidates: list[MatchCandidate]) -> MatchResult`.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/unit/core/test_matching_ladder.py
from src.core.matching.ladder import rung2_address_match


def test_rung2_matches_unique_address_after_normalization():
    # Real variant forms confirmed live: our own site_address strings use
    # "Co. Galway" / "Co Galway" / trailing "Galway"; DHLGH's
    # DevelopmentAddress uses the same variants inconsistently. Both
    # normalize to "ardgaineen".
    candidates = [
        MatchCandidate(application_ref="X", site_address="Ardgaineen, Co. Galway", site_geometry_wkt=None),
    ]
    result = rung2_address_match("Ardgaineen, Galway", candidates)
    assert result.matched is True
    assert result.rung == 2


def test_rung2_no_match_when_addresses_differ():
    candidates = [
        MatchCandidate(application_ref="X", site_address="Townparks, Co. Galway", site_geometry_wkt=None),
    ]
    result = rung2_address_match("Ardgaineen, Galway", candidates)
    assert result.matched is False
    assert result.ambiguous is False


def test_rung2_ambiguous_when_two_candidates_share_normalized_address():
    candidates = [
        MatchCandidate(application_ref="X", site_address="Ardgaineen, Co. Galway", site_geometry_wkt=None),
        MatchCandidate(application_ref="Y", site_address="Ardgaineen Co Galway", site_geometry_wkt=None),
    ]
    result = rung2_address_match("Ardgaineen, Galway", candidates)
    assert result.matched is False
    assert result.ambiguous is True


def test_rung2_no_match_when_dhlgh_address_is_none():
    candidates = [
        MatchCandidate(application_ref="X", site_address="Ardgaineen, Co. Galway", site_geometry_wkt=None),
    ]
    result = rung2_address_match(None, candidates)
    assert result.matched is False
    assert result.ambiguous is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/core/test_matching_ladder.py -v -k rung2`
Expected: FAIL with `ImportError: cannot import name 'rung2_address_match'`

- [ ] **Step 3: Write minimal implementation**

```python
# append to src/core/matching/ladder.py, after rung1_ref_match, add import at top:
from src.core.normalization.address import normalize_address


def rung2_address_match(
    dhlgh_address: str | None, candidates: list[MatchCandidate]
) -> MatchResult:
    if not dhlgh_address:
        return MatchResult(matched=False, rung=None, ambiguous=False)

    target = normalize_address(dhlgh_address)

    hits = [
        c for c in candidates
        if c.site_address and normalize_address(c.site_address) == target
    ]

    if len(hits) == 1:
        return MatchResult(matched=True, rung=2, ambiguous=False)
    if len(hits) > 1:
        return MatchResult(matched=False, rung=None, ambiguous=True)
    return MatchResult(matched=False, rung=None, ambiguous=False)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/core/test_matching_ladder.py -v -k rung2`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/core/matching/ladder.py tests/unit/core/test_matching_ladder.py
git commit -m "feat: add rung 2 (normalized address) matching function"
```

---

### Task 3: Rung 3 — geometry proximity match (DB-backed query, not a pure function)

**Files:**
- Modify: `src/core/matching/ladder.py`
- Modify: `tests/unit/core/test_matching_ladder.py` — add a DB-backed test since this rung needs PostGIS.

**Interfaces:**
- Consumes: SQLAlchemy `Session`, `Application` model (`src/core/models/application.py`), `ST_DWithin`/`ST_Distance` from `geoalchemy2.functions`.
- Produces: `rung3_geometry_match(session: Session, dhlgh_geom_wkt: str | None, authority: str, proximity_meters: float = 25.0) -> MatchResult`. Unlike rungs 1–2, this rung queries the DB directly (candidates aren't pre-loaded as plain values, since PostGIS distance computation is far cheaper done in SQL than in Python) — this asymmetry is intentional and documented in the module docstring.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/unit/core/test_matching_ladder.py
import uuid

import sqlalchemy as sa

from src.core.db.session import SessionLocal
from src.core.matching.ladder import rung3_geometry_match
from src.core.models.application import Application


def _make_application(session, application_ref, lon, lat):
    app = Application(
        id=uuid.uuid4(),
        planning_authority="Galway County Council",
        source_entity="GALWAY_COUNTY",
        application_ref=application_ref,
        applicant_name="Test",
        site_address="Test address",
        development_description="Test",
        application_type="Permission",
        planning_status_current="Received",
        date_received="2026-01-01",
        source_system="test",
        source_file="test",
        site_geometry=f"SRID=4326;POINT({lon} {lat})",
    )
    session.add(app)
    return app


def test_rung3_matches_point_within_proximity_radius():
    session = SessionLocal()
    try:
        session.execute(sa.text("DELETE FROM applications WHERE application_ref LIKE 'GEOMTEST/%'"))
        _make_application(session, "GEOMTEST/001", -9.0568, 53.2707)
        session.commit()

        # A point ~5 meters away from the seeded row (well within 25m).
        result = rung3_geometry_match(
            session,
            "SRID=4326;POINT(-9.05675 53.27074)",
            "Galway County Council",
        )
        assert result.matched is True
        assert result.rung == 3
    finally:
        session.execute(sa.text("DELETE FROM applications WHERE application_ref LIKE 'GEOMTEST/%'"))
        session.commit()
        session.close()


def test_rung3_no_match_when_no_geometry_on_dhlgh_side():
    session = SessionLocal()
    try:
        result = rung3_geometry_match(session, None, "Galway County Council")
        assert result.matched is False
        assert result.ambiguous is False
    finally:
        session.close()


def test_rung3_no_match_when_no_candidates_have_geometry():
    # Reflects real current state: applications.site_geometry is 0%
    # populated (confirmed live: 0 of 20,902 rows), so this rung must
    # cleanly report no-match rather than error when the whole table has
    # no geometry to compare against.
    session = SessionLocal()
    try:
        result = rung3_geometry_match(
            session,
            "SRID=4326;POINT(-9.0568 53.2707)",
            "Galway County Council",
        )
        assert result.matched is False
    finally:
        session.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/core/test_matching_ladder.py -v -k rung3`
Expected: FAIL with `ImportError: cannot import name 'rung3_geometry_match'`

- [ ] **Step 3: Write minimal implementation**

```python
# append to src/core/matching/ladder.py, add imports at top:
from geoalchemy2.functions import ST_DWithin, ST_GeogFromText
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.models.application import Application


def rung3_geometry_match(
    session: Session,
    dhlgh_geom_wkt: str | None,
    authority: str,
    proximity_meters: float = 25.0,
) -> MatchResult:
    if not dhlgh_geom_wkt:
        return MatchResult(matched=False, rung=None, ambiguous=False)

    hits = session.scalars(
        select(Application.id).where(
            Application.planning_authority == authority,
            Application.site_geometry.isnot(None),
            ST_DWithin(
                ST_GeogFromText(Application.site_geometry.ST_AsText()),
                ST_GeogFromText(dhlgh_geom_wkt),
                proximity_meters,
            ),
        )
    ).all()

    if len(hits) == 1:
        return MatchResult(matched=True, rung=3, ambiguous=False)
    if len(hits) > 1:
        return MatchResult(matched=False, rung=None, ambiguous=True)
    return MatchResult(matched=False, rung=None, ambiguous=False)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/core/test_matching_ladder.py -v -k rung3`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/core/matching/ladder.py tests/unit/core/test_matching_ladder.py
git commit -m "feat: add rung 3 (geometry proximity) matching function"
```

---

### Task 4: Rung 4 — trigram fuzzy match (DB-backed, surfaced for manual review only)

**Files:**
- Modify: `src/core/matching/ladder.py`
- Modify: `tests/unit/core/test_matching_ladder.py`

**Interfaces:**
- Consumes: SQLAlchemy `Session`, `Application` model, PostgreSQL `similarity()` function via `sqlalchemy.func.similarity`.
- Produces: `rung4_fuzzy_match(session: Session, dhlgh_address: str | None, authority: str, threshold: float = 0.6) -> MatchResult`. Per spec, this rung's "match" is never auto-applied — `MatchResult.matched=True` here means "candidate for manual review," and the validation-pass report (Task 5) must tag rung-4 results distinctly from rungs 1–3 in its output.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/unit/core/test_matching_ladder.py
from src.core.matching.ladder import rung4_fuzzy_match


def _make_application_with_address(session, application_ref, address):
    app = Application(
        id=uuid.uuid4(),
        planning_authority="Galway County Council",
        source_entity="GALWAY_COUNTY",
        application_ref=application_ref,
        applicant_name="Test",
        site_address=address,
        development_description="Test",
        application_type="Permission",
        planning_status_current="Received",
        date_received="2026-01-01",
        source_system="test",
        source_file="test",
    )
    session.add(app)
    return app


def test_rung4_matches_similar_address_above_threshold():
    session = SessionLocal()
    try:
        session.execute(sa.text("DELETE FROM applications WHERE application_ref LIKE 'FUZZYTEST/%'"))
        _make_application_with_address(session, "FUZZYTEST/001", "Ardgaineen Claregalway Co Galway")
        session.commit()

        result = rung4_fuzzy_match(
            session, "Ardgaineen, Claregalway, Co. Galway", "Galway County Council"
        )
        assert result.matched is True
        assert result.rung == 4
    finally:
        session.execute(sa.text("DELETE FROM applications WHERE application_ref LIKE 'FUZZYTEST/%'"))
        session.commit()
        session.close()


def test_rung4_no_match_when_no_candidates_pass_threshold():
    session = SessionLocal()
    try:
        result = rung4_fuzzy_match(
            session, "Completely unrelated string xyzzy", "Galway County Council"
        )
        assert result.matched is False
    finally:
        session.close()


def test_rung4_no_match_when_dhlgh_address_is_none():
    session = SessionLocal()
    try:
        result = rung4_fuzzy_match(session, None, "Galway County Council")
        assert result.matched is False
        assert result.ambiguous is False
    finally:
        session.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/core/test_matching_ladder.py -v -k rung4`
Expected: FAIL with `ImportError: cannot import name 'rung4_fuzzy_match'`

- [ ] **Step 3: Write minimal implementation**

```python
# append to src/core/matching/ladder.py, add import at top:
from sqlalchemy import func


def rung4_fuzzy_match(
    session: Session,
    dhlgh_address: str | None,
    authority: str,
    threshold: float = 0.6,
) -> MatchResult:
    """Last-resort fuzzy rung (spec section 9): matches here are surfaced
    for manual review, never auto-applied. Callers must tag rung-4 results
    distinctly from rungs 1-3 in any report they produce."""
    if not dhlgh_address:
        return MatchResult(matched=False, rung=None, ambiguous=False)

    hits = session.scalars(
        select(Application.id).where(
            Application.planning_authority == authority,
            Application.site_address.isnot(None),
            func.similarity(Application.site_address, dhlgh_address) >= threshold,
        )
    ).all()

    if len(hits) == 1:
        return MatchResult(matched=True, rung=4, ambiguous=False)
    if len(hits) > 1:
        return MatchResult(matched=False, rung=None, ambiguous=True)
    return MatchResult(matched=False, rung=None, ambiguous=False)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/core/test_matching_ladder.py -v -k rung4`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/core/matching/ladder.py tests/unit/core/test_matching_ladder.py
git commit -m "feat: add rung 4 (trigram fuzzy) matching function for manual review"
```

---

### Task 5: `run_ladder()` orchestrator

**Files:**
- Modify: `src/core/matching/ladder.py`
- Modify: `tests/unit/core/test_matching_ladder.py`

**Interfaces:**
- Consumes: all four rung functions above.
- Produces: `run_ladder(session: Session, dhlgh_ref: str, dhlgh_address: str | None, dhlgh_geom_wkt: str | None, authority: str, candidates: list[MatchCandidate]) -> MatchResult` — tries rung 1, then 2, then 3, then 4, stopping at the first that returns `matched=True`; if a rung is `ambiguous=True`, that also stops the ladder (an ambiguous rung is not overridden by a later rung per spec: "a rung that returns more than one candidate is treated as no match... and logged", not silently retried elsewhere) — logs which outcome occurred and returns it as-is, tagging the final `MatchResult.rung` so the caller knows which rung (if any) resolved it, and exposing ambiguity distinctly per rung via a `str` reason is deferred to the CLI report layer (Task 6) which already receives the full `MatchResult`.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/unit/core/test_matching_ladder.py
from src.core.matching.ladder import run_ladder


def test_run_ladder_stops_at_rung1_when_ref_matches():
    session = SessionLocal()
    try:
        candidates = [
            MatchCandidate(application_ref="17792", site_address="Cahernamona ,", site_geometry_wkt=None),
        ]
        result = run_ladder(
            session,
            dhlgh_ref="17792",
            dhlgh_address="Some other address entirely",
            dhlgh_geom_wkt=None,
            authority="Galway County Council",
            candidates=candidates,
        )
        assert result.matched is True
        assert result.rung == 1
    finally:
        session.close()


def test_run_ladder_falls_through_to_rung2_when_ref_fails():
    session = SessionLocal()
    try:
        candidates = [
            MatchCandidate(application_ref="99999", site_address="Ardgaineen, Co. Galway", site_geometry_wkt=None),
        ]
        result = run_ladder(
            session,
            dhlgh_ref="00000",
            dhlgh_address="Ardgaineen, Galway",
            dhlgh_geom_wkt=None,
            authority="Galway County Council",
            candidates=candidates,
        )
        assert result.matched is True
        assert result.rung == 2
    finally:
        session.close()


def test_run_ladder_reports_no_match_when_all_rungs_fail():
    session = SessionLocal()
    try:
        candidates = [
            MatchCandidate(application_ref="99999", site_address="Totally different", site_geometry_wkt=None),
        ]
        result = run_ladder(
            session,
            dhlgh_ref="00000",
            dhlgh_address="Nothing alike",
            dhlgh_geom_wkt=None,
            authority="Galway County Council",
            candidates=candidates,
        )
        assert result.matched is False
        assert result.rung is None
    finally:
        session.close()


def test_run_ladder_stops_on_ambiguous_rung_without_trying_later_rungs():
    session = SessionLocal()
    try:
        candidates = [
            MatchCandidate(application_ref="17792", site_address="A", site_geometry_wkt=None),
            MatchCandidate(application_ref="17792", site_address="B", site_geometry_wkt=None),
        ]
        result = run_ladder(
            session,
            dhlgh_ref="17792",
            dhlgh_address="A",
            dhlgh_geom_wkt=None,
            authority="Galway County Council",
            candidates=candidates,
        )
        assert result.matched is False
        assert result.ambiguous is True
    finally:
        session.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/core/test_matching_ladder.py -v -k run_ladder`
Expected: FAIL with `ImportError: cannot import name 'run_ladder'`

- [ ] **Step 3: Write minimal implementation**

```python
# append to src/core/matching/ladder.py

def run_ladder(
    session: Session,
    dhlgh_ref: str,
    dhlgh_address: str | None,
    dhlgh_geom_wkt: str | None,
    authority: str,
    candidates: list[MatchCandidate],
) -> MatchResult:
    rung1 = rung1_ref_match(dhlgh_ref, authority, candidates)
    if rung1.matched or rung1.ambiguous:
        return rung1

    rung2 = rung2_address_match(dhlgh_address, candidates)
    if rung2.matched or rung2.ambiguous:
        return rung2

    rung3 = rung3_geometry_match(session, dhlgh_geom_wkt, authority)
    if rung3.matched or rung3.ambiguous:
        return rung3

    rung4 = rung4_fuzzy_match(session, dhlgh_address, authority)
    return rung4
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/core/test_matching_ladder.py -v`
Expected: PASS (all tests in the file, 19 total)

- [ ] **Step 5: Commit**

```bash
git add src/core/matching/ladder.py tests/unit/core/test_matching_ladder.py
git commit -m "feat: add run_ladder orchestrator trying all 4 rungs in order"
```

---

### Task 6: Validation-pass CLI

**Files:**
- Create: `scripts/validate_dhlgh_matching.py`
- Test: `tests/integration/test_validate_dhlgh_matching.py`

**Interfaces:**
- Consumes: `run_ladder`, `MatchCandidate` from `src.core.matching.ladder`; `Application`, `DHLGHApplication` models; `SessionLocal` from `src.core.db.session`.
- Produces: `build_validation_report(session: Session) -> dict` with shape:
  ```python
  {
      "total_dhlgh_rows": int,
      "by_rung": {"rung_1": int, "rung_2": int, "rung_3": int, "rung_4_manual_review": int, "no_match": int, "ambiguous": int},
      "coverage": {
          "Galway City Council": {"dhlgh_count": int, "our_count": int},
          "Galway County Council": {"dhlgh_count": int, "our_count": int},
      },
      "field_quality": {
          "dhlgh_site_address_non_null_pct": float,
          "dhlgh_site_geometry_non_null_pct": float,
      },
  }
  ```

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_validate_dhlgh_matching.py
import uuid

import sqlalchemy as sa

from scripts.validate_dhlgh_matching import build_validation_report
from src.core.db.session import SessionLocal
from src.core.models.application import Application
from src.core.models.dhlgh_application import DHLGHApplication


def _cleanup(session):
    session.execute(sa.text("DELETE FROM applications WHERE application_ref LIKE 'VALTEST/%'"))
    session.execute(sa.text("DELETE FROM dhlgh_applications WHERE application_ref LIKE 'VALTEST/%'"))
    session.commit()


def test_build_validation_report_counts_rung1_match_and_no_match():
    session = SessionLocal()
    try:
        _cleanup(session)

        session.add(Application(
            id=uuid.uuid4(),
            planning_authority="Galway County Council",
            source_entity="GALWAY_COUNTY",
            application_ref="VALTEST/001",
            applicant_name="Test",
            site_address="Test address one",
            development_description="Test",
            application_type="Permission",
            planning_status_current="Received",
            date_received="2026-01-01",
            source_system="test",
            source_file="test",
        ))
        session.add(DHLGHApplication(
            id=uuid.uuid4(),
            planning_authority="Galway County Council",
            source_entity="DHLGH_NATIONAL",
            application_ref="VALTEST/001",
            development_description="Test",
            site_address="Test address one",
            planning_status_current="Received",
            date_received="2026-01-01",
            source_system="test",
        ))
        session.add(DHLGHApplication(
            id=uuid.uuid4(),
            planning_authority="Galway County Council",
            source_entity="DHLGH_NATIONAL",
            application_ref="VALTEST/999",
            development_description="Test",
            site_address="Totally unrelated address",
            planning_status_current="Received",
            date_received="2026-01-01",
            source_system="test",
        ))
        session.commit()

        report = build_validation_report(session, authority_filter="Galway County Council", ref_prefix="VALTEST/")

        assert report["by_rung"]["rung_1"] == 1
        assert report["by_rung"]["no_match"] == 1
        assert report["total_dhlgh_rows"] == 2
    finally:
        _cleanup(session)
        session.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/integration/test_validate_dhlgh_matching.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.validate_dhlgh_matching'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/validate_dhlgh_matching.py
"""
DHLGH cross-source identity matching validation pass (spec section 9,
docs/superpowers/specs/2026-07-10-dhlgh-national-source-design.md). Runs
the matching ladder (src/core/matching/ladder.py) across the full Galway
overlap between `applications` and `dhlgh_applications` and reports
per-rung match counts, per-authority coverage, and dhlgh_applications
field-quality stats.

Read-only against `applications`: this pass never writes, merges, or
upserts. Its only output is the printed/returned report dict, for a
future separate decision on whether/how to act on DHLGH data.
"""

import argparse
import logging
from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.core.db.session import SessionLocal
from src.core.matching.ladder import MatchCandidate, run_ladder
from src.core.models.application import Application
from src.core.models.dhlgh_application import DHLGHApplication

logger = logging.getLogger(__name__)

AUTHORITIES = ["Galway City Council", "Galway County Council"]


def build_validation_report(
    session: Session, authority_filter: str | None = None, ref_prefix: str | None = None
) -> dict:
    authorities = [authority_filter] if authority_filter else AUTHORITIES

    by_rung = defaultdict(int)
    coverage = {}

    for authority in authorities:
        app_query = select(Application).where(Application.planning_authority == authority)
        dhlgh_query = select(DHLGHApplication).where(DHLGHApplication.planning_authority == authority)
        if ref_prefix:
            app_query = app_query.where(Application.application_ref.like(f"{ref_prefix}%"))
            dhlgh_query = dhlgh_query.where(DHLGHApplication.application_ref.like(f"{ref_prefix}%"))

        our_rows = session.scalars(app_query).all()
        dhlgh_rows = session.scalars(dhlgh_query).all()

        candidates = [
            MatchCandidate(
                application_ref=row.application_ref,
                site_address=row.site_address,
                site_geometry_wkt=None,
            )
            for row in our_rows
        ]

        coverage[authority] = {"dhlgh_count": len(dhlgh_rows), "our_count": len(our_rows)}

        for row in dhlgh_rows:
            geom_wkt = session.scalar(select(func.ST_AsText(row.site_geometry))) if row.site_geometry is not None else None
            result = run_ladder(
                session,
                dhlgh_ref=row.application_ref,
                dhlgh_address=row.site_address,
                dhlgh_geom_wkt=geom_wkt,
                authority=authority,
                candidates=candidates,
            )
            if result.ambiguous:
                by_rung["ambiguous"] += 1
            elif result.matched and result.rung == 4:
                by_rung["rung_4_manual_review"] += 1
            elif result.matched:
                by_rung[f"rung_{result.rung}"] += 1
            else:
                by_rung["no_match"] += 1

    total_dhlgh_rows = sum(c["dhlgh_count"] for c in coverage.values())

    all_dhlgh = session.scalars(
        select(DHLGHApplication).where(DHLGHApplication.planning_authority.in_(authorities))
    ).all()
    non_null_address = sum(1 for r in all_dhlgh if r.site_address)
    non_null_geometry = sum(1 for r in all_dhlgh if r.site_geometry is not None)
    field_quality = {
        "dhlgh_site_address_non_null_pct": round(100 * non_null_address / len(all_dhlgh), 1) if all_dhlgh else 0.0,
        "dhlgh_site_geometry_non_null_pct": round(100 * non_null_geometry / len(all_dhlgh), 1) if all_dhlgh else 0.0,
    }

    return {
        "total_dhlgh_rows": total_dhlgh_rows,
        "by_rung": dict(by_rung),
        "coverage": coverage,
        "field_quality": field_quality,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    session = SessionLocal()
    try:
        report = build_validation_report(session)
        logger.info("Validation pass complete: %s", report)
        print(report)
    finally:
        session.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/integration/test_validate_dhlgh_matching.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_dhlgh_matching.py tests/integration/test_validate_dhlgh_matching.py
git commit -m "feat: add DHLGH matching validation-pass CLI and report"
```

---

### Task 7: Run the full validation pass against real data and record results

**Files:**
- None created — this task runs the Task 6 CLI against the live 22,075-row dataset and records the real output in the spec/memory, per the plan's actual goal (a report, not code).

- [ ] **Step 1: Run the full project test suite to confirm no regressions**

Run: `.venv/bin/python -m pytest -q`
Expected: all tests pass (145 previously + new tests from Tasks 1-6)

- [ ] **Step 2: Run the validation pass CLI for real**

Run: `.venv/bin/python scripts/validate_dhlgh_matching.py`
Expected: prints a report dict with `total_dhlgh_rows` close to 22,075, per-rung counts, coverage, and field_quality. Rung 3 is expected to show 0 matches (site_geometry is 0% populated on the `applications` side per Global Constraints) — this is the correct, expected outcome, not a failure to fix.

- [ ] **Step 3: Commit the report as a dated addendum to the spec**

Append a new section to `docs/superpowers/specs/2026-07-10-dhlgh-national-source-design.md` titled "## 11. Validation pass results (YYYY-MM-DD)" containing the literal printed report dict and one paragraph of interpretation (match rate per rung, whether County/City coverage matches the spec's earlier estimates, and the confirmed rung-3 zero-match finding).

```bash
git add docs/superpowers/specs/2026-07-10-dhlgh-national-source-design.md
git commit -m "docs: record DHLGH matching validation-pass results in spec"
```

---

## Self-Review Notes

- **Spec coverage:** Section 9's 4-rung ladder → Tasks 1-4. Ladder orchestration + ambiguity handling → Task 5. Validation-pass runner + report (coverage rate, match rate per rung, field quality) → Task 6. Actually running it and recording results → Task 7. "Does not implement the merge" constraint → enforced by Global Constraints and by `build_validation_report` never calling `session.add`/`session.commit` against `applications`.
- **Placeholder scan:** no TBD/TODO; every step has complete runnable code.
- **Type consistency:** `MatchCandidate` and `MatchResult` defined once in Task 1, reused verbatim by name in Tasks 2-6 without redefinition drift. `run_ladder` signature in Task 5 matches exactly how Task 6 calls it.
