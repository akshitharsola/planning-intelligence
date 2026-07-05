# Galway City normalizer: same silent-coercion bugs as County (pre-fix)

**Status:** Not started. Found during the final whole-branch review after the
County hardening plan (`2026-07-04-county-stack-hardening.md`) completed.
County is fixed and merged-ready; City still has both bugs below.

**File:** `src/pipelines/normalize.py` (Galway City weekly-lists PDF path —
sibling to `src/core/normalization/galway_county.py`, which was fixed)

---

## Bug 1 — blank `file_number` silently coerced to `""`

`normalize.py:35`
```python
application_ref=raw_row.get("file_number", ""),
```

Same defect as County's original bug, fixed in commit `e6db688`
("fix: reject County records with a blank ApplicationNumber"). `application_ref`
is half of the `(planning_authority, application_ref)` natural key used for
upsert dedup. A missing/blank `file_number` here silently becomes `""`,
so multiple such City records collide under the same natural key and
silently overwrite each other instead of failing loudly.

**Fix shape** (mirrors the County pattern exactly): clean the `file_number`
value first (strip/normalize), then validate it's non-blank, then reuse the
cleaned value in `ApplicationCreate`. Raise `ValueError` if blank, before
constructing `ApplicationCreate`.

**Required pre-step — confirm caller safety before touching `normalize_row`:**
Before raising `ValueError` for blank `file_number`, first confirm whatever
calls `normalize_row` for City (equivalent of
`scripts/ingest_galway_county.py`) already catches per-row exceptions and
logs/counts the failure instead of aborting the entire file. This is not
optional — if the caller doesn't already catch per-row exceptions, the new
`ValueError` will abort the whole ingestion run on the first blank row
instead of just skipping that one bad record, which is strictly worse than
today's silent coercion. If the caller does not yet catch per-row
exceptions, add that as part of this fix (same as Task 2 did for County).

**Missing test coverage:** `tests/unit/pipelines/test_normalize.py` has no
test for a missing/blank `file_number` today.

---

## Bug 2 — unrecognized `source_type` silently defaults to "Received"

`normalize.py:25` (also `_SOURCE_TYPE_TO_STATUS` dict at lines 12-20)
```python
status, event_type = _SOURCE_TYPE_TO_STATUS.get(source_type, ("Received", "APPLICATION_RECEIVED"))
```

Same defect as County's original bug, fixed in commit `12c7dc9`
("fix: stop county normalization silently defaulting unrecognized decisions
to Received"). Any `source_type` not in the dict's 7 known keys
(`received`, `granted`, `refused`, `invalid`, `firvalidated`, `further_recd`,
`further_reqd`) is silently treated as `"Received"` instead of being flagged
for review — an application that was actually granted/refused/withdrawn
could get miscategorized as brand new with no signal that anything went
wrong.

**Fix shape** (mirrors the County fix). State the rule explicitly so there's
no room to reintroduce a silent default later: recognized source types
(the 7 known keys) use `_SOURCE_TYPE_TO_STATUS`; anything else — including
an unrecognized string, `None`, or blank `source_type` — returns
`("Unknown/Needs Review", "STATUS_UNRECOGNIZED")`.

**Decision needed up front — blank/`None` `source_type` is in scope, not
just "unrecognized" strings.** The original note above only talks about
unrecognized *values*, which leaves blank/`None` ambiguous. Resolve this
before implementing: either (a) treat blank/`None` as invalid input that
should raise, matching the file_number treatment, or (b) fold it into the
same "Unknown/Needs Review" / `STATUS_UNRECOGNIZED" fallback as any other
unrecognized value. Recommendation: use (b) — a blank/`None` source_type is
just another case of "not a recognized key," and raising here (unlike
file_number) isn't needed to protect a dedup key, so the simpler uniform
fallback is preferable. Write the test for whichever rule is chosen so the
behavior is locked in.

**Missing test coverage:**
- No test exercises an unrecognized `source_type` string today.
- No test exercises `source_type=None` or blank `source_type` today —
  add one per the decision above.
- No regression test confirms a known-good mapping still works after the
  fallback change — add a positive test that `source_type="received"`
  still maps to `("Received", "APPLICATION_RECEIVED")`, so the fix doesn't
  accidentally alter normal behavior for recognized values.

---

## Why this wasn't in the original 3-task plan

The independent review that produced the County hardening plan happened to
cite these two failure modes using County's field names/data shape. City
has the identical bug *class* in its own normalizer, but it wasn't in scope
for that plan. Flagging here so it can be scheduled as its own
Subagent-Driven Development plan (or folded into one) once County is
verified in testing.

## Suggested next step

Once County is verified, run this through `superpowers:writing-plans` the
same way County was: two tasks (blank-file_number rejection,
unrecognized/blank-source_type fallback), each with its own
failing-test-first step, mirroring the County plan's task shape almost
verbatim. If this becomes a full implementation plan, include a final full
test-suite run and a `graphify update .` + commit step at the end, same as
the County hardening plan did, for consistency with the repo workflow.
