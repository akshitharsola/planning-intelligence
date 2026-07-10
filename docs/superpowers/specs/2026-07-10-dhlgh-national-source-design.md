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
- Deduplicating/merging DHLGH rows against existing `applications` rows
  (different `ApplicationNumber` formats are expected across sources —
  no join key has been verified yet; a future comparison pass can decide
  whether/how to merge).
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

## 9. Risks

- **OBJECTID watermark stability** — same unverified-but-adopted
  assumption already accepted for County's scraper (documented in
  `docs/superpowers/specs/2026-06-30-ingestion-cli-design.md` section 2).
  Carried over here, not re-litigated.
- **Schema drift risk**: this is a shared *national* feed maintained by
  DHLGH, not council-specific — a change in shape affects all 31
  authorities' consumers, not just ours, so it's less likely to change
  silently than a single council's ad-hoc PDF format, but the field list
  should still be spot-checked periodically.
- **No verified join key to existing `applications` table yet** — explicit
  non-goal per section 2. `ApplicationNumber` formats have not been
  compared across sources; that comparison is future work, not assumed
  here.
