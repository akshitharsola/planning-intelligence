# Chat Search Filter Bugs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix two bugs in the natural-language chat search path
(`src/services/chat_service.py` + `src/services/application_service.py`)
that cause real, present applications to be silently reported as "no
applications matched" — discovered live: asking about a known application
(`26/20`, "Mr Kevin Burke", Galway City Council, visible on the dashboard)
returned zero matches.

**Architecture:** Two independent, additive fixes to the existing
extract-filters → search → summarize pipeline in `chat_service.py` and
`application_service.py`. No schema changes, no new files. Both fixes are
narrowing/validation changes to existing filter handling — they can only
make previously-zero-result queries succeed; they cannot break a query that
currently returns correct results.

**Tech Stack:** Python, SQLAlchemy ORM (`Application` model), pytest,
Postgres (tests hit a real DB per existing convention in this test suite —
no mocks).

## Global Constraints

- Test runner: `/opt/anaconda3/bin/python -m pytest` (the plain `python3` /
  `pytest` on PATH does not have the project's dependencies installed —
  this is a pre-existing environment quirk, not something to fix).
- Ignore these test files when running the suite — they fail to *collect*
  (not run) due to missing system packages (`psycopg2`, `pdfplumber`),
  which is pre-existing and out of scope:
  `--ignore=tests/unit/core/test_application_natural_key.py
  --ignore=tests/unit/core/test_ingestion_state.py
  --ignore=tests/unit/parsers/test_galway_city_pdf_lines.py
  --ignore=tests/unit/services/test_chat_extraction_prompt.py`
- Integration tests in `tests/integration/test_chat_service.py` and
  `tests/integration/test_application_service.py` run against a real
  Postgres DB (via `src.core.db.session.SessionLocal`) — follow the
  existing `_cleanup()` / `_seed()` / `PREFIX` pattern in each file
  exactly; do not introduce mocks for the DB layer.
- `_FILTER_KEYS` in `chat_service.py` is the fixed tuple of allowed filter
  keys: `("planning_authority", "planning_status_current",
  "application_type", "date_received_from", "date_received_to", "q")`.
  Do not add a new key to this tuple as part of either fix below — both
  fixes work within the existing keys.
- Do not modify `main` directly — do the work in an isolated worktree/branch
  per `superpowers:using-git-worktrees`, and merge back only after review,
  same as the City/County normalizer work.
- If this plan is executed via subagent-driven-development, run the full
  scoped test suite (with the `--ignore` flags above) once after both
  tasks are complete, then run `graphify update .` and commit
  `graphify-out/` alongside the final commit, per repo convention
  (`/Users/akshitharsola/CLAUDE.md`).

---

## Why this happened (context for both tasks)

Two independent bugs compounded on the same live query
(`"From Galway City Council for application 26/20 of \"Mr Kevin Burke\",
what's the status?"`):

1. The LLM extracted `q: "26/20 Mr Kevin Burke"` — but `application_service.search()`'s
   `q` filter only ever checks `applicant_name`, `site_address`, and
   `development_description` (`src/services/application_service.py:44-50`).
   It never checks `application_ref`. Any keyword search that includes an
   application reference number can never match, even though the
   application_ref is right there in the row and is exactly the kind of
   thing a user would ask about by name.
2. The LLM also extracted `application_type: "E"` — a value that is not in
   the allowed type list the prompt itself lists ("one of {types}"). `"E"`
   was applied as a hard `==` filter (`application_service.py:29-31`),
   which excluded the correct row (whose actual `application_type` is
   `"Retention"`). The extraction prompt does not forbid guessing an
   out-of-list value, and nothing downstream validates the value before
   using it as a filter.

Both fixes are independent: Task 1 widens what `q` can match; Task 2 makes
`application_type` filtering robust to a hallucinated/invalid value. Either
fix alone would have prevented the observed failure being *permanent*, but
both are real defects and both must be fixed.

---

### Task 1: Make `q` also match `application_ref`

**Files:**
- Modify: `src/services/application_service.py:44-50` (the `q` filter loop
  inside `search()`)
- Test: `tests/integration/test_application_service.py`

**Interfaces:**
- Consumes: `Application.application_ref` (existing column, `Mapped[str]`,
  non-nullable — see `src/core/models/application.py:21`)
- Produces: no new interface; `search()`'s existing signature
  `search(db: Session, filters: dict, page: int, page_size: int) -> tuple[list[Application], int]`
  is unchanged. Task 2 does not depend on this task's internals.

- [ ] **Step 1: Write the failing test**

Add to `tests/integration/test_application_service.py` (uses the existing
`PREFIX`, `_cleanup()`, `_seed()`, `_insert()` helpers already in that
file — do not redefine them):

```python
def test_search_q_matches_application_ref():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            rows, total = search(session, {"q": f"{PREFIX}/0001"}, page=1, page_size=25)
        finally:
            session.close()
        refs = {r.application_ref for r in rows}
        assert f"{PREFIX}/0001" in refs
        assert f"{PREFIX}/0002" not in refs
    finally:
        _cleanup()


def test_search_q_matches_application_ref_case_insensitive_partial():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            rows, total = search(session, {"q": "0001"}, page=1, page_size=25)
        finally:
            session.close()
        refs = {r.application_ref for r in rows}
        assert f"{PREFIX}/0001" in refs
        assert f"{PREFIX}/0002" not in refs
    finally:
        _cleanup()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
/opt/anaconda3/bin/python -m pytest tests/integration/test_application_service.py::test_search_q_matches_application_ref tests/integration/test_application_service.py::test_search_q_matches_application_ref_case_insensitive_partial -v
```
Expected: both FAIL — `f"{PREFIX}/0001" in refs` is False, because
`application_ref` is not yet part of the `q` filter's `or_(...)` clause.

- [ ] **Step 3: Implement the fix**

In `src/services/application_service.py`, locate the `q` filter block:

```python
    q = filters.get("q")
    if q:
        for keyword in q.split():
            pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    Application.applicant_name.ilike(pattern),
                    Application.site_address.ilike(pattern),
                    Application.development_description.ilike(pattern),
                )
            )
```

Add `Application.application_ref` to the `or_(...)` clause:

```python
    q = filters.get("q")
    if q:
        for keyword in q.split():
            pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    Application.applicant_name.ilike(pattern),
                    Application.site_address.ilike(pattern),
                    Application.development_description.ilike(pattern),
                    Application.application_ref.ilike(pattern),
                )
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
/opt/anaconda3/bin/python -m pytest tests/integration/test_application_service.py -v
```
Expected: PASS, all tests in the file including the two new ones and the
pre-existing ones (`test_search_q_multiple_keywords_all_must_match`, etc. —
confirm none of those regress, since `application_ref` is now also checked
for every keyword, which only ever adds matches, never removes them).

- [ ] **Step 5: Commit**

```bash
git add tests/integration/test_application_service.py src/services/application_service.py
git commit -m "fix: let chat/search q filter also match application_ref"
```

---

### Task 2: Reject a hallucinated `application_type` instead of filtering on it

**Files:**
- Modify: `src/services/chat_service.py` (`_extract_filters`, and the
  module-level context available to it)
- Test: `tests/integration/test_chat_service.py`

**Interfaces:**
- Consumes: `dashboard_service.get_type_breakdown(db)` (already imported
  and used in `_extraction_prompt` — see
  `src/services/chat_service.py:31`), which returns a list of dicts with a
  `"label"` key.
- Produces: `_extract_filters(client, db, question) -> dict` keeps its
  existing signature and only ever returns a *subset* of what the LLM
  proposed (never adds new keys). `answer_question()`'s use of
  `_extract_filters` is unchanged.

**Why validate here, not in the prompt alone:** the prompt already says
`application_type` must be "one of" the allowed labels, but the live
failure proves the LLM does not reliably obey that instruction. Prompt
wording is not a enforcement mechanism; the fix must reject an
out-of-list value in code, the same way `_FILTER_KEYS` already rejects
unknown *keys* (see the existing test
`test_answer_question_ignores_unknown_filter_keys_from_llm` in
`tests/integration/test_chat_service.py`, which this task's tests sit
alongside).

- [ ] **Step 1: Write the failing test**

Add to `tests/integration/test_chat_service.py` (uses the existing
`FakeLLMClient`, `PREFIX`, `_cleanup()`, `_seed()` helpers already in that
file — do not redefine them). `_seed()` inserts one row with
`application_type='Permission'`, so an LLM reply claiming
`application_type: "E"` (not a real type in this dataset) must be dropped,
leaving only `q` as the effective filter:

```python
def test_answer_question_drops_hallucinated_application_type():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            client = FakeLLMClient(
                replies=[
                    '{"application_type": "E", "q": "chattestville"}',
                    "There is one new dwelling permission granted in Chattestville.",
                ]
            )
            result = answer_question(session, "What's new in Chattestville?", client=client)
        finally:
            session.close()

        # "E" is not a real application_type in this dataset -> must be dropped,
        # not applied as a filter, so the real (Permission-typed) row still matches.
        assert "application_type" not in result["filters"]
        assert result["total"] == 1
        assert result["applications"][0].application_ref == f"{PREFIX}/0001"
    finally:
        _cleanup()


def test_answer_question_keeps_valid_application_type():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            client = FakeLLMClient(
                replies=[
                    '{"application_type": "Permission", "q": "chattestville"}',
                    "There is one new dwelling permission granted in Chattestville.",
                ]
            )
            result = answer_question(session, "What's new in Chattestville?", client=client)
        finally:
            session.close()

        # "Permission" IS a real application_type in this dataset -> must be kept.
        assert result["filters"]["application_type"] == "Permission"
        assert result["total"] == 1
    finally:
        _cleanup()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
/opt/anaconda3/bin/python -m pytest tests/integration/test_chat_service.py::test_answer_question_drops_hallucinated_application_type tests/integration/test_chat_service.py::test_answer_question_keeps_valid_application_type -v
```
Expected: `test_answer_question_drops_hallucinated_application_type` FAILS
(`"application_type" not in result["filters"]` is False, and/or `total`
comes back `0` because `"E"` was applied as a hard filter). The second
test is expected to already PASS (it documents current-correct behavior
for a valid type) — confirm this so Step 3 does not accidentally regress
it.

- [ ] **Step 3: Implement the fix**

In `src/services/chat_service.py`, `_extract_filters` currently reads:

```python
def _extract_filters(client: LLMClient, db: Session, question: str) -> dict:
    system = _extraction_prompt(db)
    reply = client.chat(system, question)
    parsed = extract_json(reply)
    if not parsed:
        return {}
    return {k: v for k, v in parsed.items() if k in _FILTER_KEYS and v}
```

Change it to also drop `application_type` if it is not one of the allowed
labels (recompute the allowed set the same way `_extraction_prompt` does,
via `dashboard_service.get_type_breakdown`):

```python
def _extract_filters(client: LLMClient, db: Session, question: str) -> dict:
    system = _extraction_prompt(db)
    reply = client.chat(system, question)
    parsed = extract_json(reply)
    if not parsed:
        return {}
    filters = {k: v for k, v in parsed.items() if k in _FILTER_KEYS and v}

    allowed_types = {r["label"] for r in dashboard_service.get_type_breakdown(db) if r["label"]}
    if "application_type" in filters and filters["application_type"] not in allowed_types:
        del filters["application_type"]

    return filters
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
/opt/anaconda3/bin/python -m pytest tests/integration/test_chat_service.py -v
```
Expected: PASS, all tests in the file including both new tests and the
pre-existing ones (in particular
`test_answer_question_ignores_unknown_filter_keys_from_llm` must still
pass — confirm the new validation only touches `application_type`, not the
existing unknown-key filtering).

- [ ] **Step 5: Commit**

```bash
git add tests/integration/test_chat_service.py src/services/chat_service.py
git commit -m "fix: drop hallucinated application_type instead of filtering on it"
```

---

### Task 3: Full-suite verification and graphify update

**Files:** none (verification-only task)

- [ ] **Step 1: Run the full scoped test suite**

```bash
/opt/anaconda3/bin/python -m pytest tests/unit tests/integration \
  --ignore=tests/unit/core/test_application_natural_key.py \
  --ignore=tests/unit/core/test_ingestion_state.py \
  --ignore=tests/unit/parsers/test_galway_city_pdf_lines.py \
  --ignore=tests/unit/services/test_chat_extraction_prompt.py \
  -q
```
Expected: all tests pass, 0 failures.

- [ ] **Step 2: Update graphify and commit**

```bash
graphify update .
git add graphify-out/
git commit -m "chore: update graphify after chat search filter fixes"
```

---

## Self-review notes

- Spec coverage: both bugs identified from the live screenshots are
  covered — Task 1 fixes `q` not matching `application_ref`; Task 2 fixes
  `application_type` hallucination. No other filter keys
  (`planning_authority`, `planning_status_current`, date range) showed a
  failure in the observed screenshots, so they are out of scope for this
  plan.
- Both fixes are additive/narrowing at the SQL/filter level — Task 1 only
  adds an `OR` clause (strictly widens matches), Task 2 only removes an
  invalid key before it reaches `search()` (strictly narrows what's
  filtered on, never adds a new false-positive filter). Neither can
  regress a currently-passing query.
- Types and signatures: `search()`'s signature is unchanged in Task 1;
  `_extract_filters()`'s signature and return type (`dict`) are unchanged
  in Task 2 — later code (`answer_question`) needs no changes.
