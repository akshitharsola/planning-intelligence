# City Normalizer Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the two County-style silent-coercion bugs identified in the
Galway City normalizer during the final whole-branch review of the County
hardening plan (see
`docs/superpowers/plans/2026-07-04-galway-city-normalizer-gaps.md` for the
original finding and reviewer feedback). Same bug *class* as County, already
fixed there in commits `12c7dc9` and `e6db688`; this plan applies the
identical pattern to City's normalizer.

**Architecture:** All work happens on branch
`worktree-city-normalizer-hardening` (worktree at
`.claude/worktrees/city-normalizer-hardening`), branched from `main` at
commit `5e4179b` (the just-merged County hardening + web dashboard work).
Two independent fixes in `src/pipelines/normalize.py`:
1. `normalize_row` must reject a record with a blank/missing `file_number`
   instead of silently coercing it to `""`, since `application_ref` is half
   of the natural key used for upsert dedup.
2. `_SOURCE_TYPE_TO_STATUS.get(source_type, ...)` must never silently
   default an unrecognized (or blank/`None`) `source_type` to `"Received"` —
   it must fall back to `("Unknown/Needs Review", "STATUS_UNRECOGNIZED")`
   instead, mirroring County's `_derive_status` fallback exactly.

**Already verified (no task needed for this):** `scripts/ingest_galway_city.py`
lines 80-107 already wrap `normalize_row(...)` in a per-row `try/except`
that logs and counts (`failed += 1`) rather than aborting the whole file,
and does not mark the file ingested if any row failed (`file_failed == 0`
check at line 109). This is the exact caller-safety precondition the
reviewer asked to confirm before allowing `normalize_row` to raise
`ValueError` — confirmed satisfied, no caller changes required.

**Tech Stack:** Python 3.11, Pydantic schemas, pytest. No DB/Alembic
involvement — `normalize_row` is a pure function.

## Global Constraints

- Working directory for all commands:
  `/Users/akshitharsola/Documents/AiAgentic/planning-intelligence/.claude/worktrees/city-normalizer-hardening`
- Test runner: `/opt/anaconda3/bin/python -m pytest` (project has no local
  venv/poetry in this environment; the anaconda Python 3.13 install has all
  deps needed for `tests/unit/pipelines/` — confirmed working).
- Scope test runs to the affected test file and the broader non-DB unit
  suite; do NOT attempt `tests/unit/core/test_application_natural_key.py`,
  `tests/unit/core/test_ingestion_state.py`,
  `tests/unit/parsers/test_galway_city_pdf_lines.py`, or
  `tests/unit/services/test_chat_extraction_prompt.py` — these fail to
  collect in this environment due to missing `psycopg2`/`pdfplumber`
  system packages, unrelated to this plan's scope. Confirmed pre-existing
  and out of scope.
- Follow TDD: write the failing test, run it, watch it fail for the right
  reason, then implement.
- Every task ends with the scoped test suite green:
  `/opt/anaconda3/bin/python -m pytest tests/unit --ignore=tests/unit/core/test_application_natural_key.py --ignore=tests/unit/core/test_ingestion_state.py --ignore=tests/unit/parsers/test_galway_city_pdf_lines.py --ignore=tests/unit/services/test_chat_extraction_prompt.py`
- After each commit, run `graphify update .` and stage `graphify-out/`
  alongside the code change in the same commit (per this repo's
  `CLAUDE.md`).
- Do not modify `main` — all commits land on
  `worktree-city-normalizer-hardening`.

---

### Task 1: Reject blank/missing `file_number` instead of silently coercing to `""`

**Files:**
- Modify: `src/pipelines/normalize.py:33-45` (the `normalize_row` function)
- Test: `tests/unit/pipelines/test_normalize_galway_city.py`

**Interfaces:**
- Consumes: nothing new. `normalize_row`'s only caller is
  `scripts/ingest_galway_city.py:81`, which already catches per-row
  exceptions (see Architecture note above) — no caller changes needed.
- Produces: `normalize_row(...)` raises `ValueError` instead of returning an
  `ApplicationCreate` with `application_ref=""` when `file_number` is
  missing or blank. Signature is unchanged.

**Fix shape** (mirrors County's `e6db688` exactly — clean first, then
validate, then reuse the cleaned value):

```python
def normalize_row(raw_row: dict, source_type: str, region_config: dict,
                   source_file: str) -> ApplicationCreate:
    file_number = str(raw_row.get("file_number", "")).strip()
    if not file_number:
        raise ValueError(
            f"City record missing file_number (source_file={source_file!r}); "
            "refusing to normalize a row with a blank natural-key component."
        )

    status, event_type = _SOURCE_TYPE_TO_STATUS.get(...)  # unchanged here, see Task 2
    ...
    return ApplicationCreate(
        ...
        application_ref=file_number,
        ...
    )
```

- [ ] **Step 1: Write the failing tests**

Add these two test functions to the end of
`tests/unit/pipelines/test_normalize_galway_city.py`:

```python
import pytest

from src.pipelines.normalize import normalize_row


def test_normalize_row_rejects_missing_file_number():
    raw_row = {
        "applicant": "Test Applicant",
        "app_type": "P",
        "description": "test",
    }
    with pytest.raises(ValueError, match="file_number"):
        normalize_row(raw_row, source_type="received", region_config=REGION_CONFIG,
                      source_file="Weekly Lists - Planning Applications Received.pdf")


def test_normalize_row_rejects_blank_file_number():
    raw_row = {
        "file_number": "   ",
        "applicant": "Test Applicant",
        "app_type": "P",
        "description": "test",
    }
    with pytest.raises(ValueError, match="file_number"):
        normalize_row(raw_row, source_type="received", region_config=REGION_CONFIG,
                      source_file="Weekly Lists - Planning Applications Received.pdf")
```

(Add the `import pytest` line once at the top of the file if not already
present — check first, do not duplicate.)

Run the scoped test command from Global Constraints. Both new tests must
fail — confirm the failure is "ApplicationCreate was returned instead of
ValueError raised" (or a Pydantic validation error from an empty
`application_ref`), not a collection error or unrelated failure.

- [ ] **Step 2: Implement the fix**

Apply the fix shape above to `src/pipelines/normalize.py`. Keep every other
field construction in `normalize_row` unchanged — only change how
`file_number` is resolved and validated, and reuse the cleaned
`file_number` value in the `application_ref=` argument instead of the raw
`raw_row.get("file_number", "")` call.

- [ ] **Step 3: Run the full scoped suite and confirm green**

Run the scoped test command from Global Constraints. Confirm the two new
tests pass and the existing two tests in
`test_normalize_galway_city.py` (`test_normalize_row_received_maps_to_application_received_event`,
`test_normalize_row_granted_sets_decision_fields`) still pass unchanged —
both already provide non-blank `file_number` values, so they must not
regress.

- [ ] **Step 4: `graphify update .`, commit**

Commit message should explain the natural-key dedup risk (same rationale
as County's `e6db688`), and note that the caller already catches this
per-row.

---

### Task 2: Reject/flag unrecognized or blank `source_type` instead of silently defaulting to "Received"

**Files:**
- Modify: `src/pipelines/normalize.py:22-35` (`_SOURCE_TYPE_TO_STATUS` dict
  and its lookup in `normalize_row`)
- Test: `tests/unit/pipelines/test_normalize_galway_city.py`

**Interfaces:**
- Consumes: nothing new. `_match_source_type` in
  `scripts/ingest_galway_city.py:29-43` already returns `None` (not an
  empty string) when no `pdf_patterns` key matches, and the caller at line
  69 already skips the row entirely (`continue`) with a warning log when
  `source_type is None` — so `normalize_row` itself only ever receives a
  non-`None` `source_type` string from that caller today. This task's fix
  must still handle `source_type=None` or blank defensively inside
  `normalize_row` (see decision rule below), both because the function is
  unit-tested directly with arbitrary inputs and to avoid a future caller
  silently regressing this guarantee.
- Produces: no signature change. `normalize_row` raises no exception here
  (unlike Task 1) — returns `("Unknown/Needs Review", "STATUS_UNRECOGNIZED")`
  instead of `("Received", "APPLICATION_RECEIVED")` for the fallback case.

**The decision rule this task implements — state it exactly this way, no
room for a silent default to be reintroduced later:**

> Recognized source types (the 7 known keys in `_SOURCE_TYPE_TO_STATUS`:
> `received`, `granted`, `refused`, `invalid`, `firvalidated`,
> `further_recd`, `further_reqd`) use `_SOURCE_TYPE_TO_STATUS`. Anything
> else — including an unrecognized string, `None`, or a blank/whitespace
> string — returns `("Unknown/Needs Review", "STATUS_UNRECOGNIZED")`.

This resolves the blank/`None` ambiguity the original gaps doc left open:
blank/`None` is folded into the same fallback as any other unrecognized
value (option (b) from the reviewer discussion) — it is not treated as a
raise-worthy input like Task 1's `file_number`, because `source_type` is
not part of the natural key.

**Fix shape:**

```python
_SOURCE_TYPE_TO_STATUS = {
    "received": ("Received", "APPLICATION_RECEIVED"),
    "granted": ("Granted", "DECISION_GRANTED"),
    "refused": ("Refused", "DECISION_REFUSED"),
    "invalid": ("Invalid", "APPLICATION_INVALID"),
    "firvalidated": ("Received", "APPLICATION_RECEIVED"),
    "further_recd": ("Further Info", "FURTHER_INFORMATION_RECEIVED"),
    "further_reqd": ("Further Info", "FURTHER_INFORMATION_REQUESTED"),
}

_UNRECOGNIZED_STATUS = ("Unknown/Needs Review", "STATUS_UNRECOGNIZED")


def normalize_row(raw_row: dict, source_type: str, region_config: dict,
                   source_file: str) -> ApplicationCreate:
    ...
    status, event_type = _SOURCE_TYPE_TO_STATUS.get(
        (source_type or "").strip(), _UNRECOGNIZED_STATUS
    )
    ...
```

Note `(source_type or "").strip()` — this treats `None` and whitespace-only
strings the same as any other non-matching key, falling through to
`_UNRECOGNIZED_STATUS` via the dict's default, without a separate
branch/raise.

- [ ] **Step 1: Write the failing tests**

Add these three test functions to the end of
`tests/unit/pipelines/test_normalize_galway_city.py`:

```python
def test_normalize_row_unrecognized_source_type_flags_for_review():
    raw_row = {
        "file_number": "24/9999",
        "applicant": "Test Applicant",
        "app_type": "P",
        "description": "test",
    }
    app = normalize_row(raw_row, source_type="some_new_pdf_category",
                        region_config=REGION_CONFIG, source_file="test.pdf")
    assert app.planning_status_current == "Unknown/Needs Review"
    assert app.status_event_type == "STATUS_UNRECOGNIZED"


def test_normalize_row_blank_source_type_flags_for_review():
    raw_row = {
        "file_number": "24/9998",
        "applicant": "Test Applicant",
        "app_type": "P",
        "description": "test",
    }
    app = normalize_row(raw_row, source_type="", region_config=REGION_CONFIG,
                        source_file="test.pdf")
    assert app.planning_status_current == "Unknown/Needs Review"
    assert app.status_event_type == "STATUS_UNRECOGNIZED"


def test_normalize_row_received_source_type_still_maps_correctly():
    # Regression guard: confirms the fallback change above doesn't alter
    # behavior for a known-good recognized source_type.
    raw_row = {
        "file_number": "24/9997",
        "applicant": "Test Applicant",
        "app_type": "P",
        "description": "test",
    }
    app = normalize_row(raw_row, source_type="received", region_config=REGION_CONFIG,
                        source_file="test.pdf")
    assert app.planning_status_current == "Received"
    assert app.status_event_type == "APPLICATION_RECEIVED"
```

Run the scoped test command. The first two must fail (today they'd assert
`"Received"`/`"APPLICATION_RECEIVED"` incorrectly returned instead of the
expected `"Unknown/Needs Review"`/`"STATUS_UNRECOGNIZED"`); the third
should already pass before the fix (it's the regression guard) — confirm
it passes both before and after Step 2.

- [ ] **Step 2: Implement the fix**

Apply the fix shape above. Do not change any of the 7 existing dict
entries — only the fallback used by `.get(...)`.

- [ ] **Step 3: Run the full scoped suite and confirm green**

Run the scoped test command. Confirm all 5 new tests (2 from Task 1, 3 from
this task) plus the original 2 pre-existing tests in this file all pass —
7 tests total in `test_normalize_galway_city.py`.

- [ ] **Step 4: `graphify update .`, commit**

Commit message should state the explicit fallback rule from this task's
decision-rule section, and note this mirrors County's `12c7dc9`.

---

## Final Step (after both tasks)

- [ ] Run the full scoped non-DB unit suite one more time from the
  Global Constraints command and confirm all tests pass.
- [ ] Dispatch the final whole-branch code review
  (`superpowers:requesting-code-review`'s reviewer template) comparing
  `5e4179b..HEAD` on this branch.
- [ ] Use `superpowers:finishing-a-development-branch` to merge
  `worktree-city-normalizer-hardening` into `main`.
