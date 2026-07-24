# DHLGH National Planning Dataset — New Independent Source

Date: 2026-07-10

## 1. Purpose

Our two existing Galway sources both have structural address gaps: County's
own ArcGIS feed (`config/galway/county.yaml`,
`src/sources/galway/county/scraper.py`) only provides a free-text
`Location` townland string, and City's weekly PDF lists
(`config/galway/city.yaml`, `src/sources/galway/city/scraper.py`) bury the
address inside the `description` field with no dedicated column. Neither
source publishes a real Eircode/postcode field. Live verification against
the DHLGH (Department of Housing, Local Government and Heritage) national
planning dataset confirmed:

- `DevelopmentPostcode` exists in the schema but is **0% populated** for
  both Galway City (0 of 3,397) and Galway County (0 of 18,649) — Eircode
  is not recoverable from this or any other free official source found.
  That question is closed; a commercial GeoDirectory address→Eircode
  lookup is the only remaining path, out of scope here.
- `DevelopmentAddress` **is** populated with clean structured addresses
  (e.g. "15 Emerson Avenue , Salthill , Galway"), a real improvement over
  both existing sources.
- City coverage in DHLGH goes back to **2012**, vs. our own City scraper's
  practical limit of ~2022-07 (weekly-list archive retention).
- Records carry real **polygon site geometry** (`rings` in the ArcGIS
  response) plus `ITMEasting`/`ITMNorthing` — the first genuine geolocation
  data available for Galway from any source so far.
- Native **appeal fields** exist (`AppealRefNumber`, `AppealStatus`,
  `AppealDecision`, `AppealDecisionDate`, `AppealSubmittedDate`) — directly
  useful for the "An Bord Pleanála" layer on the project roadmap, at zero
  extra scraping cost.

Endpoint (confirmed live):
`https://services.arcgis.com/NzlPQPKn5QF9v2US/arcgis/rest/services/IrishPlanningApplications/FeatureServer/1`

## 2. Scope decision: additive, not a replacement

This is a **new, fully independent source module and a new database
table**. `GalwayCityScraper`, `GalwayCountyScraper`, the `applications`
table, existing CLIs, and everything the chat/dashboard queries today are
**not touched**. Rationale (explicit user decision): keep today's working
pipeline completely undisturbed, and give DHLGH a real trial period as a
separate, comparable dataset — if it doesn't hold up, dropping it costs
nothing, and reverting to the original two-scraper setup requires no
cleanup.

Out of scope for this design:
- Deduplicating/merging DHLGH rows against existing `applications` rows.
  Section 9 documents a concrete matching ladder and exit criteria for a
  separate validation-pass task, but that task is not part of this
  ingestion work and this design does not implement or run it.
- Eircode enrichment via any paid API (GeoDirectory) — separate future
  decision, not blocked by this work.
- Backfilling other counties — this covers Galway City + County only,
  filtered at the query level.

## 3. New source module

`src/sources/dhlgh/scraper.py` — `DHLGHScraper(BaseSource)`. Same shape as
`GalwayCountyScraper` (`src/sources/galway/county/scraper.py:22`) because
the DHLGH endpoint is the same kind of source: a public, no-auth ArcGIS
Feature Service, paginated by an incrementing OBJECTID watermark. No files
to download, so `acquire()` is a passthrough returning its input
unchanged, exactly as County's does today.

`discover()` differs from County's in one respect: the `where` clause
must filter to `PlanningAuthority IN ('Galway City Council', 'Galway
County Council')` in addition to the watermark predicate, since this feed
is national (covers all 31 local authorities) and we only want Galway.

## 4. New config

`config/dhlgh/galway.yaml`, same shape as `config/galway/county.yaml`:

```yaml
source_entity: DHLGH_NATIONAL
planning_authorities:
  - "Galway City Council"
  - "Galway County Council"
arcgis_query_url: "https://services.arcgis.com/NzlPQPKn5QF9v2US/arcgis/rest/services/IrishPlanningApplications/FeatureServer/1/query"
watermark_field: "OBJECTID"
page_size: 1000
out_fields:
  - OBJECTID
  - PlanningAuthority
  - ApplicationNumber
  - DevelopmentDescription
  - DevelopmentAddress
  - DevelopmentPostcode
  - ITMEasting
  - ITMNorthing
  - ApplicationStatus
  - ApplicationType
  - Decision
  - ReceivedDate
  - WithdrawnDate
  - DecisionDate
  - DecisionDueDate
  - GrantDate
  - ExpiryDate
  - AppealRefNumber
  - AppealStatus
  - AppealDecision
  - AppealDecisionDate
  - AppealSubmittedDate
  - FIRequestDate
  - FIRecDate
  - LinkAppDetails
  - SiteId
returnGeometry: true
```

`returnGeometry: true` is new relative to County's config (County queries
with `returnGeometry=false`, `src/sources/galway/county/scraper.py:68`) —
the DHLGH layer's value-add includes the polygon, so this source's query
must request it.

## 5. New database table

New Alembic migration
`src/core/db/migrations/versions/0004_create_dhlgh_applications.py`
(`down_revision = '0003'`), following the existing `<n>_<verb>_<subject>`
naming convention:

```sql
CREATE TABLE dhlgh_applications (
    id UUID PRIMARY KEY,
    planning_authority VARCHAR NOT NULL,
    source_entity VARCHAR NOT NULL,
    application_ref VARCHAR NOT NULL,
    development_description VARCHAR NOT NULL,
    site_address VARCHAR,
    site_postcode VARCHAR,
    site_geometry GEOMETRY(GEOMETRY, 4326),
    itm_easting DOUBLE PRECISION,
    itm_northing DOUBLE PRECISION,
    application_type VARCHAR,
    planning_status_current VARCHAR NOT NULL,
    decision VARCHAR,
    date_received DATE NOT NULL,
    decision_due_date DATE,
    decision_date DATE,
    withdrawn_date DATE,
    grant_date DATE,
    expiry_date DATE,
    appeal_ref_number VARCHAR,
    appeal_status VARCHAR,
    appeal_decision VARCHAR,
    appeal_decision_date DATE,
    appeal_submitted_date DATE,
    fi_request_date DATE,
    fi_received_date DATE,
    official_detail_url VARCHAR,
    site_id VARCHAR,
    source_system VARCHAR NOT NULL,
    source_ingested_at TIMESTAMP NOT NULL DEFAULT now(),
    raw_payload_json JSON NOT NULL,
    CONSTRAINT uq_dhlgh_application_natural_key
        UNIQUE (planning_authority, application_ref)
);

CREATE INDEX idx_dhlgh_applications_site_geometry
    ON dhlgh_applications USING GIST (site_geometry);
CREATE INDEX ix_dhlgh_applications_planning_status_current
    ON dhlgh_applications (planning_status_current);
CREATE INDEX ix_dhlgh_applications_date_received
    ON dhlgh_applications (date_received);
```

New SQLAlchemy model: `src/core/models/dhlgh_application.py` (mirrors
`src/core/models/application.py`'s style — `geoalchemy2.Geometry` for
`site_geometry`).

No `ApplicationEvent`-equivalent table for this source in this pass —
DHLGH's `ApplicationStatus`/`Decision`/appeal fields already carry
enough lifecycle state per row that a separate event log isn't needed to
get value from this data; can be added later if the comparison against
`application_events` turns out to matter.

Ingestion-state tracking reuses the existing `ingestion_state` table
(`src/core/db/migrations/versions/0002_create_ingestion_state.py`) with a
new `region` value (`dhlgh_galway`) — that table is already
region-generic (`region TEXT PRIMARY KEY, watermark TEXT`), so no schema
change needed there.

## 6. New schema, normalize, resolve, publish

**New Pydantic schema** `DHLGHApplicationCreate` in
`src/core/schemas/dhlgh_application.py` — not a reuse of the existing
`ApplicationCreate` (`src/core/schemas/application.py:12`). The field sets
diverge enough (postcode, ITM coordinates as separate columns, five appeal
fields, no `market_entity`/`commuter_belt_flag` market layer, no
`other_regulatory_flags`) that forcing them into one schema would mean
every consumer handling a pile of `Optional` fields that only apply to one
source. Follows the same `model_config = ConfigDict(extra="forbid")`
convention.

**New normalize function** `normalize_dhlgh_row()` in
`src/pipelines/normalize.py` (co-located with `normalize_row()` and
`normalize_county_row()`) — maps raw ArcGIS `attributes` dict + WKT-ready
geometry into `DHLGHApplicationCreate`. Reuses `_parse_date()` and other
existing private helpers in that module as-is.

**New resolve function** `resolve_and_upsert_dhlgh()` in
`src/pipelines/resolve.py` — same dedup-by-natural-key pattern as
`resolve_and_upsert()` (`src/pipelines/resolve.py:15`), keyed on
`(planning_authority, application_ref)` against `dhlgh_applications`. No
event emission (per section 5).

**Publish**: reuses `publish()` (`src/pipelines/publish.py`) unchanged —
it already takes a `region` string and record counts, no source-specific
logic to fork.

## 7. New ingestion CLI

`scripts/ingest_dhlgh.py` — mirrors the structure of
`scripts/ingest_galway_county.py`. Its orchestration function,
`run_dhlgh_ingestion()`, wires `discover() → normalize_dhlgh_row() →
resolve_and_upsert_dhlgh() → publish()`, using the OBJECTID watermark
from `ingestion_state` under region `dhlgh_galway` for incremental re-runs.
Given the endpoint returns ~22,000 Galway rows in one filtered query
(rather than requiring per-file downloads like City), no chunked/paced
variant is needed here — this is a small number of paginated GET requests
against a single ArcGIS endpoint, not ~1,200 individual file fetches like
the City PDF backfill. A single run is expected to complete quickly.

## 8. Testing

- Unit tests for `normalize_dhlgh_row()`: covers geometry present/absent,
  empty postcode (expected, not an error), appeal fields present/absent,
  date parsing.
- Unit test for `resolve_and_upsert_dhlgh()`: insert then re-run with a
  changed status updates the existing row rather than duplicating (same
  pattern as existing `resolve_and_upsert` tests).
- Integration test: fake ArcGIS response fixture → full
  `run_dhlgh_ingestion()` → assert row counts and a couple of known-good
  field values land correctly in `dhlgh_applications`.
- No live-network test against the real DHLGH endpoint in the automated
  suite (matches existing convention for County's own ArcGIS source).

## 9. Cross-source identity: matching ladder and validation pass

This section responds to reviewer feedback: pending cross-source identity
is not a footnote, it's a real, demonstrated risk. Verified during spec
review by querying the live DHLGH endpoint and comparing against our own
`applications` table:

- DHLGH `ApplicationNumber` for Galway City looks like `2660243` (no
  slash), while our own City `application_ref` (scraped from council PDF
  file numbers) is `YY/NNN` or `YY/NNNNN`, e.g. `23/194`, `24/60030`.
  These are **not directly comparable strings**.
- **Confirmed collision, not hypothetical**: the literal string `2660243`
  already exists in our own `applications` table today — as a **Galway
  County** record ("Tonagarraun, Corrandulla, Co. Galway", received
  2026-02-17), a completely different case from DHLGH's `2660243` under
  Galway City Council ("7 Lower Canal Road, Galway", received 2026-07-08).
  A naive string-equality join on `application_ref` alone, without also
  requiring `planning_authority` to match, would silently merge two
  unrelated applications.
- **The "insert a slash after 2 digits" transform floated in an earlier
  draft of this section is not reliable and must not be assumed.**
  Checked against real County data: our own `applications` table has
  County refs of visibly different shapes in the same result set —
  `163`, `1611` (older, pre-2020ish, no year prefix apparent), `26170`
  (5 digits), and `2661119` (7 digits) all appear as distinct County
  `application_ref` values within days of each other in 2026. DHLGH's own
  County `ApplicationNumber` values include both `26170` (matches our
  5-digit shape exactly, unslashed) and `2661138`-style 7-digit values in
  the same query result. City and County do not share one predictable
  digit-count-to-format rule, and neither does a single county's own
  history over time. This is proof that identity resolution needs a
  deliberate, tested procedure — and that the normalization rule itself,
  not just the matching ladder around it, must be derived from real
  fixtures rather than assumed from a handful of samples.

**Deterministic matching ladder** (each rung attempted only if the
previous one fails to find a unique match; a rung that returns more than
one candidate is treated as no match, not a match, and logged):

1. `planning_authority` (exact) + `application_ref` (normalized via the
   `normalize_application_ref()` helper defined below).
2. `planning_authority` + normalized address match (via the
   `normalize_address()` helper defined below).
3. `planning_authority` + geometry proximity, where both sides have
   coordinates (DHLGH polygon centroid vs. our — currently absent —
   `site_geometry`; only usable once/if a source populates our side too).
4. Fuzzy text match (trigram similarity, reusing the existing
   `gin_trgm_ops` indexes already present on `applications.site_address`
   and `applications.development_description`) as a last resort,
   surfaced for manual review rather than auto-merged.

**This design does not implement the ladder or run the validation pass.**
It documents both, plus the two normalization helpers below, so the
follow-up validation-pass task (tracked separately, not folded into this
ingestion work) has a concrete, testable starting point instead of an ad
hoc one. The validation pass's job is to run the ladder against the full
Galway overlap and report, per rung, how many DHLGH rows matched — not to
perform any merge or write to `applications`.

### 9.1 `normalize_application_ref()` — first-class tested component

Per reviewer feedback, this is **not** a one-line regex assumed correct.
Given the confirmed evidence in this section that ref formats vary by
authority, by era within the same authority, and possibly by source, this
helper's own job is split into two honestly-scoped parts:

- A **rule-based transform** for shapes we can already demonstrate from
  real data (e.g. `YY` + sequence → `YY/NNNNN`, confirmed to match some
  current City refs), implemented as a small pure function with **no
  network or DB access**, so it is trivially unit-testable in isolation.
- An explicit **"could not normalize" outcome** (not an exception, not a
  silent pass-through) for any input that doesn't match a known rule —
  the caller (the future validation pass) is required to log these and
  fall through to rung 2 of the ladder rather than guess.

Required unit test fixtures, built from real refs pulled from our own
`applications` table and the live DHLGH endpoint during this design's
review (not synthetic examples):

| Input (`ApplicationNumber`) | Authority | Expected output | Basis |
|---|---|---|---|
| `2660243` | Galway City Council | `26/60243` | City 2026 refs use `YY/60NNN` (verified: `24/60030`, `23/60030` exist in our own table) |
| `26170` | Galway County Council | **cannot normalize — pass through unnormalized as `26170`** | Confirmed both our own table and DHLGH itself use this 5-digit shape for County; no year/slash structure to insert |
| `2661119` | Galway County Council | **cannot normalize** (flag as ambiguous) | Same authority, same rough time period as `26170` above, but 7 digits — proves County does not have one stable ref shape, so this helper must not force a rule onto it |
| `163` | Galway County Council | **cannot normalize** | Pre-2020ish short numeric refs with no discernible year prefix, seen in our own 2016 data |
| `24/60030` | Galway City Council | `24/60030` (already normalized; identity) | Confirms the function is idempotent on inputs already in our own `application_ref` shape |

The test suite must assert on this exact table (or its evolved version, if
more fixtures are found before the validation-pass task starts) — not on
invented examples — precisely because the point of this component is to
encode what we've actually verified, not what seems plausible.

### 9.2 `normalize_address()` — canonical recipe

For rung 2 to be deterministic and reproducible (reviewer's second
request), the recipe is fixed as an ordered sequence of steps, applied
identically to both `DevelopmentAddress` (DHLGH) and `site_address`
(ours):

1. Lowercase the full string.
2. Strip all punctuation except internal hyphens in place names (e.g.
   keep "cul-de-sac"-style names intact; drop commas, periods, apostrophes
   elsewhere).
3. Collapse repeated whitespace to a single space; trim leading/trailing
   whitespace.
4. Normalize known abbreviation variants to one canonical form via a
   fixed lookup table, e.g. `co.` / `co` / `county` → `county`, `rd` →
   `road`, `st` → `street` — table to be built from real observed
   variants in the Galway address strings (already visible in samples
   collected during this review: "Co. Galway", "Co Galway", "County
   Galway" all appear as variants of the same thing).
5. Drop trailing standalone `"galway"` / `"co. galway"` / `"county
   galway"` tokens if the rest of the string is non-empty (both sources
   redundantly append the county name to nearly every address; keeping it
   would bias every comparison toward false positives since almost all
   Galway addresses would partially match on that token alone).

Two normalized addresses are considered a match only if they are
**exactly equal** after this recipe — rung 2 is deliberately not fuzzy;
fuzzy comparison is reserved for rung 4, using the existing trigram
indexes, specifically so the two rungs have different, clearly-understood
precision/recall trade-offs rather than one blurry in-between heuristic.

**Trial-period exit criteria** (also reviewer-requested, to make "is
DHLGH worth keeping" measurable rather than a vibe check), computed after
the validation pass runs:

- **Coverage rate**: DHLGH row count vs. our existing row count, per
  authority (already known from section 1: DHLGH's 3,397 City / 18,649
  County vs. our 527 City / 20,375 County — City coverage is a clear win,
  County is roughly comparable and worth re-checking after normalization).
- **Match rate**: percentage of our existing `applications` rows that
  find a unique match in `dhlgh_applications` via the ladder above, broken
  down by which rung resolved each match.
- **Field quality**: percentage of `dhlgh_applications` rows with a
  non-null `site_address`, and separately with non-null `site_geometry`
  (both already know to be materially better than our current sources per
  section 1, but should be measured on the full ingested set, not the
  15-row samples used during spec review).

## 10. Other risks

- **OBJECTID watermark stability** — same unverified-but-adopted
  assumption already accepted for County's scraper (documented in
  `docs/superpowers/specs/2026-06-30-ingestion-cli-design.md` section 2).
  Carried over here, not re-litigated.
- **Schema drift risk**: this is a shared *national* feed maintained by
  DHLGH, not council-specific — a change in shape affects all 31
  authorities' consumers, not just ours, so it's less likely to change
  silently than a single council's ad-hoc PDF format, but the field list
  should still be spot-checked periodically.
- **`ApplicationNumber` normalization only covers some observed shapes,
  by design** — section 9.1's fixture table already shows City's `YY/60NNN`
  refs are normalizable but several real County ref shapes (`26170`,
  `2661119`, `163`) are not, from evidence gathered in this review, not
  assumption. The open risk is scale, not correctness-in-principle: the
  validation pass may surface additional shapes neither this design nor
  its fixtures anticipated, in which case `normalize_application_ref()`
  gets new fixtures and rules added incrementally — it must never be
  extended by loosening rung 1 to accept low-confidence guesses, since
  that reintroduces the exact silent-merge risk this section exists to
  prevent.

## 11. Validation pass results (2026-07-24)

Ran `scripts/validate_dhlgh_matching.py` (Task 6) against the live,
fully-ingested dataset. Full project test suite (166 tests) passed with
no regressions immediately before this run.

```python
{
    'total_dhlgh_rows': 22075,
    'by_rung': {
        'no_match': 2502,
        'ambiguous': 2709,
        'rung_2': 1574,
        'rung_4_manual_review': 410,
        'rung_1': 14880,
    },
    'coverage': {
        'Galway City Council': {'dhlgh_count': 3401, 'our_count': 527},
        'Galway County Council': {'dhlgh_count': 18674, 'our_count': 20375},
    },
    'field_quality': {
        'dhlgh_site_address_non_null_pct': 100.0,
        'dhlgh_site_geometry_non_null_pct': 100.0,
    },
}
```

**Interpretation.**

Of the 22,075 DHLGH rows, 14,880 (67.4%) matched at rung 1 (exact
`application_ref`, normalized), a further 1,574 (7.1%) matched at rung 2
(normalized address) after rung 1 failed, and 410 (1.9%) surfaced at rung
4 (fuzzy trigram) for manual review only — never auto-applied, per
section 9's design. 2,709 rows (12.3%) hit a rung that returned more than
one candidate and were correctly treated as ambiguous rather than
force-matched, and 2,502 (11.3%) found no candidate at any rung. Combined
resolved rate (rung 1 + rung 2, i.e. matches confident enough to use
without manual review) is 74.5% of all DHLGH rows. Note this is the
DHLGH-side match rate (how many DHLGH rows found a match in our
`applications` table); section 9.2's trial exit criteria framed "match
rate" the other way round (percentage of *our* `applications` rows that
find a match in DHLGH) — the two are related but not identical given the
count mismatch below, and a future pass could compute the inverse
direction if that number becomes decision-relevant.

**Rung 3 (geometry proximity) produced zero matches, as expected and
predicted by this section before the run**: a live query against
`applications` confirms `site_geometry` is populated on 0 of 20,902
Galway City/County rows. Rung 3 has no usable candidates until some
future source populates our side; this is not a bug in the ladder, and
the `by_rung` dict correctly omits a `rung_3` key entirely (a
`defaultdict` — rungs with zero occurrences never get a key rather than
appearing as `0`) rather than reporting a fabricated zero.

**Coverage vs. the section 9.2 estimates** made during spec review (DHLGH
3,397 City / 18,649 County vs. our 527 City / 20,375 County): the live
run shows 3,401 City / 18,674 County, close to the earlier estimate with
minor drift attributable to ongoing DHLGH ingestion between spec review
(2026-07-12) and this run (2026-07-24). City coverage remains the clear
win called out in section 1 (DHLGH has ~6.5x more City rows than we do);
County coverage is roughly comparable in raw count (18,674 vs. 20,375)
but the match-rate breakdown above shows most County overlap resolves
cleanly at rung 1, consistent with County `application_ref` values being
more directly comparable between the two sources than City's format
mismatch (section 9's original motivating example).

**Field quality**: 100.0% of DHLGH rows have both non-null `site_address`
and non-null `site_geometry`, matching section 1's claim that DHLGH's
field quality is materially better than our current sources on both
dimensions, now confirmed on the full ingested set rather than the
15-row sample used during spec review.

**On the 12.3% ambiguous rate**: this is a substantial minority and worth
flagging as an open question rather than a settled result — it means
roughly 1 in 8 DHLGH rows currently have multiple same-authority
candidates matching by ref or address, none of which the ladder will
auto-resolve (correctly, per the "ambiguous is not a match" rule in
section 9's ladder definition). No investigation of *why* the ambiguity
rate is this high (e.g. common duplicate patterns in the underlying data)
was done as part of this task; that remains open for a follow-up if the
ambiguous bucket needs to shrink before any downstream use of DHLGH
matches.
