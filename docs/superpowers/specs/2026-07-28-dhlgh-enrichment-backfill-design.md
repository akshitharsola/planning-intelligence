# DHLGH Enrichment Backfill — Design

## Context

The DHLGH cross-source identity matching ladder (spec
`2026-07-10-dhlgh-national-source-design.md`, section 9) is fully
implemented and validated: `src/core/matching/ladder.py` runs 4 rungs
(exact ref, exact address, geometry proximity, trigram fuzzy) and
`scripts/validate_dhlgh_matching.py` produces a read-only report of
match rates against the live 22,075-row DHLGH dataset.

That validation pass stops at "report per rung" — it never writes
anything back to `applications`. This leaves the original problem
DHLGH was ingested to solve (spec section 1: `applications.site_address`
/ `site_geometry` coverage gaps) technically unaddressed: the match
information exists but nothing acts on it.

This spec covers the missing piece: a one-off backfill that enriches
`applications` rows with DHLGH data wherever the ladder finds a
confident match.

## Goal

Backfill `applications.site_address` and `applications.site_geometry`
from `dhlgh_applications` for rows where our own data is missing that
field and the matching ladder finds a unique, high-confidence match.

## Scope decisions

- **Which rungs write:** only rung 1 (exact `application_ref`) and
  rung 2 (exact normalized address). Rung 3 (geometry proximity) is
  currently a no-op for Galway (0% `site_geometry` coverage, confirmed
  in section 11 of the DHLGH spec) so excluding it costs nothing today.
  Rung 4 (trigram fuzzy) is explicitly documented as manual-review-only
  in its own docstring and is never used for automatic writes.
  Ambiguous matches (any rung) are never used for writes.
- **Overwrite policy:** only fill fields that are currently `NULL`.
  `site_address` and `site_geometry` are each checked and enriched
  independently — never overwrite a non-null existing value. DHLGH is
  a backfill source, not a source of truth that supersedes our own
  scraped data.
- **Run mode:** a manually-invoked one-off script, not wired into the
  weekly ingestion pipeline (`com.planning-intelligence.weekly-ingestion.plist`).
  Recurring automation is a separate future decision made after this
  backfill has been run once and its results reviewed.

## Design

### `scripts/enrich_from_dhlgh.py`

Modeled directly on the existing `scripts/validate_dhlgh_matching.py`
(same session/query/ladder-invocation pattern), split into a
plan/apply pair so a write only happens after an explicit `--apply`:

**`build_enrichment_plan(session, authority_filter=None) -> list[dict]`**

For each `dhlgh_applications` row (scoped to `AUTHORITIES` unless
`authority_filter` narrows it, same as the validation script):

1. Run `run_ladder()` against the candidate `applications` rows for
   that authority (same candidate-building logic as
   `build_validation_report`).
2. Skip unless `result.matched and result.rung in (1, 2)` (excludes
   ambiguous, no-match, rung 3, rung 4).
3. For the matched `applications` row, check `site_address` and
   `site_geometry` independently. For each one that is currently
   `NULL` and has a non-null value on the DHLGH side, add a planned
   update: `{application_id, field, new_value, source_dhlgh_ref, rung}`.
4. Return the full list of planned updates (empty list if nothing
   qualifies).

This function performs **no writes** — same read-only guarantee as
the validation pass.

**`apply_enrichment_plan(session, plan) -> int`**

Takes the plan produced above and applies each planned update via a
targeted `UPDATE` (fetch the `Application` row by id, set only the
planned field, no touching of unrelated columns), inside a single
transaction, one `session.commit()` at the end. Returns the number of
fields updated. If the plan is empty, does nothing and commits nothing.

**CLI:**

```
python scripts/enrich_from_dhlgh.py            # dry-run (default): builds and prints the plan, does not call apply
python scripts/enrich_from_dhlgh.py --apply     # builds the plan, then applies it, prints count of fields updated
```

Dry-run output: total planned updates, broken down by field
(`site_address` vs `site_geometry`) and by rung (1 vs 2), plus a
handful of example rows (application_ref, field, old value `None`,
new value) so the count can be sanity-checked before committing to
`--apply`.

### Testing

- **Unit tests** (fixture-based, same pattern as
  `test_matching_ladder.py`) for `build_enrichment_plan`:
  - a rung-1 match with a null `site_address` on our side produces a
    planned update
  - a rung-2 match with a null `site_geometry` on our side produces a
    planned update
  - a match where our side already has a non-null `site_address`
    produces no planned update for that field (but may still plan an
    update for `site_geometry` if that one is null)
  - a rung-3 match never appears in the plan
  - a rung-4 match never appears in the plan
  - an ambiguous result never appears in the plan
- **Integration test** against real Postgres for `apply_enrichment_plan`:
  build a plan with a mix of fields, apply it, then assert only the
  planned fields changed and every other column (including fields that
  were already non-null) is byte-identical to before.

### Manual functional test (after implementation, required, not automatable)

1. Run `scripts/enrich_from_dhlgh.py` (dry-run) against the live DB,
   review the printed plan and counts for plausibility.
2. Run with `--apply`.
3. Start the chat UI (`chat.html` / `chat_service.py`) and ask about an
   address that was previously null and should now be populated;
   confirm it surfaces correctly.
4. Spot-check by hand (not aggregate stats): one rung-1 enriched row
   and one rung-2 enriched row, comparing the new `applications` value
   against the source `dhlgh_applications` row directly in the DB.

## Explicitly out of scope

- Wiring this into the weekly ingestion pipeline (future decision).
- Any change to rung 3/4 behavior or thresholds.
- Surfacing `dhlgh_applications` as a second, independent source in
  chat for rows that never match (the 11.3% no-match rows) — that is
  the alternative/complementary design this spec deliberately did not
  choose; may be revisited separately.
- Investigating the 12.3% ambiguous rate (already flagged as an open
  question in DHLGH spec section 11, unrelated to this backfill).
