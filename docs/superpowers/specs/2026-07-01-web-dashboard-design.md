# Web Dashboard v1 — Design

## Context

The repo has a mature Python + SQLAlchemy + Postgres/PostGIS ingestion
foundation (Galway City + County scrapers, normalize -> resolve -> publish
pipeline, canonical `Application`/`ApplicationEvent` models — see
`graphify-out/GRAPH_REPORT.md`). There is no web/presentation layer yet;
`src/services/` exists but is empty.

Real data currently in Postgres: ~20,329 planning applications, 2016–2026,
Galway City + County only.

## Goal

Build the smallest useful local web dashboard that shows this real data is
genuine and traceable. Prioritize credibility, provenance, and speed of
implementation over visual polish. Local-only for now — no deployment.

## Non-goals (explicitly out of scope)

- Maps or geometry-based UI (`site_geometry` not displayed)
- Geocoding work
- RAG/chat features
- Authentication/authorization
- Background jobs
- Cloud deployment
- Multi-council onboarding changes
- Market derivation beyond what already exists (`market_entity`,
  `commuter_belt_flag` not displayed)
- Any redesign of parser/pipeline architecture
- Changes to ingestion logic (unless trivially required for stats exposure —
  none identified)

## Stack constraints

- Reuse existing Python + SQLAlchemy + Postgres stack, nothing new added to
  the data layer.
- FastAPI + Jinja2 templates + one CSS file + one JS file. No React, Vue,
  Next.js, or any frontend build tool.
- Charts via Chart.js loaded from CDN.
- Query the canonical `Application` model directly — no new ORM abstraction
  layer.
- New dependencies (added to `pyproject.toml`): `fastapi`, `uvicorn[standard]`,
  `jinja2`. `python-multipart` is NOT needed (filters are GET forms, not
  multipart POST).

## Field names

The canonical `Application` model (`src/core/models/application.py`) uses
snake_case field names. All service/query/template code uses these exact
names — no renaming:

```
planning_authority, source_entity, application_ref, application_ref_type,
applicant_name, site_address, site_locality, site_county, site_geometry,
development_description, application_type, planning_status_current,
status_event_type, date_received, decision_due_date, decision_date,
further_information_flag, protected_structure_flag, eia_eis_flag,
other_regulatory_flags, official_detail_url, official_documents_url,
source_system, source_file, source_ingested_at, raw_payload_json,
market_entity, commuter_belt_flag
```

The natural key is `planning_authority` + `application_ref` (already
enforced by a DB unique constraint).

## Architecture

```
src/web/
  main.py                          # FastAPI app, routes, get_db dependency
  templates/
    dashboard.html
    application_detail.html
    partials/
      application_table.html
  static/
    app.css
    app.js

src/services/
  dashboard_service.py
  application_service.py
```

- DB access reuses `src.core.db.session.SessionLocal` (already exists,
  unchanged) via a FastAPI `get_db` dependency with try/finally close.
- Run locally: `uvicorn src.web.main:app --reload`.
- Service modules are plain functions taking a `Session` and returning
  dicts/lists/ORM rows — no repository classes, no new abstraction layer.

## Routes

### `GET /`

Dashboard page. Query params (all optional): `planning_authority`,
`planning_status_current`, `application_type`, `date_received_from`,
`date_received_to`, `q`, `page` (default 1), `page_size` (default 25).

Renders:
- KPI cards: total application count, distinct `planning_authority` count,
  coverage date range (`min`/`max` of `date_received`), latest update
  (`max(source_ingested_at)`).
- 3 charts (Chart.js, data inlined as JSON in the template):
  monthly applications received, status breakdown, application type
  breakdown.
- Filter form (plain HTML GET, full-page reload on submit).
- Paginated applications table, rendered via
  `partials/application_table.html` so it can later be swapped to
  HTMX/fetch without restructuring the page.

### `GET /applications/{planning_authority}/{application_ref}`

Detail page. Both path segments are URL-encoded/decoded. Exact match against
the natural key. Returns 404 (`HTTPException(404)`) if no matching row.

Displays: `planning_authority`, `application_ref`, `applicant_name`,
`site_address`, `site_locality`, `site_county`, `development_description`,
`application_type`, `planning_status_current`, `date_received`,
`decision_due_date`, `decision_date`, `further_information_flag`,
`protected_structure_flag`, `eia_eis_flag`, `source_system`, `source_file`,
`source_ingested_at`, `official_detail_url` (if present),
`official_documents_url` (if present).

## Service layer

### `dashboard_service.py`

- `get_summary(db) -> dict`: total count, distinct `planning_authority`
  count, min/max `date_received`, max `source_ingested_at`.
- `get_monthly_counts(db) -> list[dict]`: `[{"label": "2026-01", "value": 123}, ...]`
  grouped by year-month of `date_received`.
- `get_status_breakdown(db) -> list[dict]`: grouped by
  `planning_status_current`.
- `get_type_breakdown(db) -> list[dict]`: grouped by `application_type`.

### `application_service.py`

- `search(db, filters, page, page_size) -> tuple[list[Application], int]`:
  filtered, paginated rows plus total count. `q` performs case-insensitive
  (`ILIKE`) matching across `applicant_name`, `site_address`,
  `development_description` (OR'd together).
- `get_by_natural_key(db, planning_authority, application_ref) -> Application | None`.

## Testing (modest, not a full harness)

- Service query tests: summary, chart breakdowns, search filtering,
  pagination math.
- Route smoke test: `GET /` returns 200 and renders expected KPI/table
  structure.
- Route tests: valid detail page returns 200 with expected fields; unknown
  natural key returns 404.
- One filter-correctness test (e.g. filtering by `planning_authority`
  narrows results as expected).
- One pagination test (page 2 returns the next slice, total count is
  correct).

## README

Add a short section to `README.md` covering: install web deps, ensure
Postgres is running with data ingested, run
`uvicorn src.web.main:app --reload`, open `http://localhost:8000`.

## Execution steps

1. Add dependencies to `pyproject.toml`.
2. Create `src/services/dashboard_service.py` and
   `src/services/application_service.py`.
3. Create `src/web/main.py` with `get_db` dependency and both routes.
4. Create templates and static files.
5. Wire dashboard data end-to-end (KPIs, charts, table, filters).
6. Wire detail page end-to-end.
7. Add tests per the section above.
8. Add README run instructions.

## Definition of done

- App runs locally with `uvicorn src.web.main:app --reload`.
- `/` renders KPI cards, 3 charts, filter form, and a paginated table from
  real DB data.
- Detail route works via `planning_authority` + `application_ref`, 404s
  cleanly on unknown keys.
- Provenance fields (`source_system`, `source_file`, `source_ingested_at`,
  `official_detail_url`, `official_documents_url`) are clearly shown on the
  detail page.
- Filters work using canonical snake_case field names.
- Basic tests pass.
- Implementation stays small, readable, and consistent with existing repo
  structure (no new abstraction layers, no ingestion-logic changes).
