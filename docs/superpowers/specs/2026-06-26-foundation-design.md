# Foundation Design — Planning-Intelligence Platform

Date: 2026-06-26

## 1. Purpose

Stand up the `planning-intelligence` repository as the generalized foundation
described in `docs/foundation-development-plan.md`: a multi-council planning
data ingestion platform for Ireland, starting from the existing Galway City
proof-of-concept (`duffy-main-repo-main`) and generalizing it to support many
councils, parser families, and city/metro/county market layers.

This design covers:

- Repo scaffold and tech stack
- Canonical schema implementation
- Porting the Galway City source from duffy, and building Galway County
  fresh (different acquisition method, no existing code to port)
- A custom Claude Code skill (`/onboard-council`) for the recurring
  "add a new council" workflow (used for every council *after* Galway)
- Two subagents (`source-onboarding`, `parser-dev`) that the skill dispatches to
- GitHub hosting and collaborator setup

Out of scope for this foundation: the chat/RAG layer (`chat_app.py`,
`rag_engine.py`, `embedder.py` in duffy), insight/update/detail service UIs,
and any council beyond Galway (City + County). These are explicitly
deferred — see section 10.

## 2. Tech Stack

- **Language:** Python (matches duffy POC and dev plan's `pyproject.toml`).
- **Database:** PostgreSQL + PostGIS, run locally via `docker-compose.yml`.
  Chosen over SQLite because the canonical schema's `site_geometry` field and
  the market-derivation step (section 6.6 of the dev plan — assigning
  applications to `GALWAY_CITY` / `GALWAY_METRO` / `GALWAY_COUNTY` via
  polygon/point-in-polygon checks) need real GIS queries, not just string
  matching against a fixed town list. SQLite would require a later schema
  migration anyway; doing it now avoids rework.
- **ORM:** SQLAlchemy for models, Pydantic for canonical schema validation
  (matches dev plan section 7 folder layout).
- **PDF parsing:** `pdfplumber` (already proven in duffy for Galway City).
- **Migrations:** Alembic.

## 3. Repo Layout

Adapts `docs/foundation-development-plan.md` section 7 layout with one
structural change from the original plan: **county-level grouping** instead
of a flat `authorities/` list. Ireland's local authorities are themselves
organized by county, and the dev plan's market entities are already named
`GALWAY_CITY` / `GALWAY_METRO` / `GALWAY_COUNTY` — grouping by county means
each new region (Cork, Dublin, ...) gets one top-level folder containing all
of its city/metro/county variants, instead of files for the same region
scattered across a flat list. Also adds `.claude/` for the project-scoped
skill and subagents, and `docker-compose.yml` for local Postgres+PostGIS.

```text
planning-intelligence/
├── README.md
├── pyproject.toml
├── docker-compose.yml
├── .env.example
├── .gitignore
├── .claude/
│   ├── skills/
│   │   └── onboard-council/
│   │       └── SKILL.md
│   └── agents/
│       ├── source-onboarding.md
│       └── parser-dev.md
├── docs/
│   ├── foundation-development-plan.md
│   ├── strategy-report.md
│   ├── source-inventory.md
│   ├── schema.md
│   └── market-layering.md
├── config/
│   ├── settings.py
│   ├── logging.yaml
│   └── galway/
│       ├── city.yaml
│       └── county.yaml
├── data/
│   └── galway/
│       ├── city/
│       │   └── temp/        # raw downloads — purge-safe once loaded into Postgres
│       └── county/
│           └── temp/        # raw downloads — purge-safe once loaded into Postgres
├── src/
│   ├── core/{models,db,schemas,normalization,lifecycle,geo}/
│   ├── parsers/{pdf_lines,pdf_text_fallback,docx_state_machine,pdf_ocr}/
│   ├── sources/
│   │   ├── base/
│   │   └── galway/
│   │       ├── city/
│   │       └── county/
│   ├── pipelines/{discover,acquire,extract,normalize,resolve,publish}.py
│   ├── markets/
│   │   ├── registry.py
│   │   └── galway/
│   │       ├── city.py
│   │       ├── metro.py
│   │       └── county.py
│   └── services/{search_service,update_service,insight_service}.py
└── tests/{fixtures,unit,integration,regression}/
```

Every future council follows the same pattern: `config/<county>/`,
`data/<county>/<region>/temp/`, `src/sources/<county>/<region>/`,
`src/markets/<county>/<region>.py`. The `/onboard-council` skill (section 6)
scaffolds new counties this way automatically.

### 3.1 Raw data storage: `temp/`, not a permanent archive

Duffy's current convention stores raw downloads under a single external
root (`DUFFY_ROOT`, defaulting to `E:\Duffy`, overridable via `DATA_DIR`) with
no expectation of cleanup. This foundation deliberately does **not** carry
that forward. Raw PDFs/DOCX are an ingestion **buffer**, not the system of
record — once `pipelines/normalize.py` + `resolve.py` have written an
application's data into Postgres, the raw file has no further purpose beyond
re-parsing during parser development.

So each region gets a `data/<county>/<region>/temp/` folder, named `temp` to
make the intent explicit: contents are disposable. A future cleanup job (or
manual `rm`) can clear `temp/` once rows are confirmed persisted, without
losing anything — `source_file` + `raw_payload_json` on the `applications`
table (section 4) already preserve enough provenance to know what was
ingested, even after the original file is deleted. `temp/` is `.gitignore`d.

## 4. Canonical Schema & Lifecycle

Implements dev plan sections 4 and 5 directly:

- `Application` SQLAlchemy model — core, lifecycle/status, provenance, and
  market-layer fields as specified (section 4.1–4.4).
- `ApplicationEvent` model — one row per lifecycle event
  (`APPLICATION_RECEIVED`, `DECISION_GRANTED`, etc., per section 5.1).
- Natural key for resolving duplicate rows across reports:
  `planning_authority + application_ref` (section 6.5).
- Pydantic schemas in `src/core/schemas/` mirror the SQLAlchemy models for
  validation at the `normalize` pipeline stage, so a parser's raw row output
  must satisfy the canonical schema before it can be persisted.

## 5. Galway City (ported) and Galway County (built fresh)

### 5.1 Galway City — port from duffy

Confirmed from duffy's actual code: Galway City's "scraper" is not HTML
scraping at all — it hits the **filegator REST API** behind
`files.galwaycity.ie` directly with three plain HTTP calls (auth → list dir
→ download). This becomes the first concrete `sources/galway/city`
implementation:

| Duffy file | New home | Adaptation needed |
|---|---|---|
| `scraper.py` | `src/sources/galway/city/scraper.py` | Same filegator API calls; output path goes to `data/galway/city/temp/` instead of `DUFFY_ROOT`. |
| `pdf_extractor.py` | `src/parsers/pdf_lines/galway_city.py` | Becomes the first concrete implementation of the `pdf_table_lines` parser family interface. |
| `data_processor.py` | Split across `src/pipelines/normalize.py` + `src/core/normalization/` | Row-mapping logic (FILE NUMBER → `application_ref`, etc., from duffy's `COLUMN_MAP`) becomes the canonical normalization mapping for Galway City. |
| `database.py` | `src/core/db/` | Re-targeted from SQLite ad-hoc tables to the canonical Postgres schema. |
| `folder_walker.py`, `config.py` | Reference only | Logic folded into `config/galway/city.yaml` + `src/pipelines/discover.py`. |
| `chat_app.py`, `rag_engine.py`, `embedder.py`, `query_engine.py`, `report_generator.py` | **Not ported** | Out of scope — see section 10. |

The original `duffy-main-repo-main` directory is left untouched as a reference;
nothing is deleted from it.

### 5.2 Galway County — built fresh, no duffy precedent

Galway County uses a **different acquisition method** than City — there is
no filegator-style API. Per the dev plan (section 3.2), County's sources are:

- A weekly-list webpage with plain PDF download links (requires HTML
  scraping to find the links — City's API approach doesn't apply).
- An ePlanning listing endpoint (`SearchListing/RECEIVED`, etc.) with a
  rolling 7–42 day window — closer to a paginated API.
- A planning-files document search/viewer.
- ArcGIS open-data layers for historical/geospatial backfill.

Since duffy never built a County integration, this foundation pass builds
`src/sources/galway/county/` from scratch:

- An HTML-scraping acquirer for the weekly-list PDF links (new code, no
  port).
- A parser under the `pdf_table_lines` family initially (same family as
  City, per dev plan section 3.2's "rich geospatial context" note implying
  similar tabular structure) — the `source-onboarding` subagent's first job
  on County is to fetch real sample PDFs and confirm this assumption before
  `parser-dev` builds against them. If County's PDFs turn out to lack a text
  layer or use a different structure, the parser family gets reclassified at
  that point rather than assumed up front.
- `config/galway/county.yaml` capturing both the weekly-list URL and the
  ePlanning endpoint for future use.

County's parser is genuinely new work in this pass, not a stub — both City
and County should have working ingestion by the end of this foundation.

## 6. Custom Skill: `/onboard-council`

Project-scoped skill at `.claude/skills/onboard-council/SKILL.md`. Invoked as
`/onboard-council <county_slug> <region_slug>` (e.g. `/onboard-council cork
city`). Galway City and County are built directly in this foundation pass
(section 5) rather than through the skill — the skill exists for every
council added *after* the foundation lands.

Workflow:

1. Check if `config/<county>/<region>.yaml` already exists — if so, treat as
   an update/resume rather than a fresh onboarding.
2. Dispatch the **`source-onboarding`** subagent to research the region's
   planning-list site(s): URL(s), file format, update cadence, and to pull
   down 1–2 sample files into `data/<county>/<region>/temp/samples/`.
   Findings get appended to `docs/source-inventory.md`.
3. Based on the subagent's findings, classify the parser family:
   `pdf_table_lines`, `pdf_table_text_fallback`, `docx_state_machine`, or
   `pdf_ocr_pipeline` (per dev plan section 6.3 and duffy's
   `multi_city_comparison.md` precedent).
4. Scaffold `config/<county>/<region>.yaml` (source URLs, parser family,
   filename patterns) and `src/sources/<county>/<region>/` (thin source
   module following the `src/sources/base/` interface).
5. Dispatch the **`parser-dev`** subagent with the sample files and chosen
   parser family to build/iterate the parser under
   `src/parsers/<family>/<county>_<region>.py`, with a unit test in
   `tests/unit/parsers/` that asserts the sample file extracts into valid
   canonical raw rows.
6. Report back: what was scaffolded, parser test status, and what still needs
   human review (e.g. ambiguous column mappings, market-derivation rules for
   the new region).

The skill does not run the ingestion pipeline end-to-end or write to the
database — it only scaffolds code and config for human review.

## 7. Subagents

### `source-onboarding`
- **Input:** council name/slug.
- **Job:** Research the council's official planning website(s): weekly list
  pages, ePlanning portals, open-data/GIS layers. Determine file format
  (PDF with text layer / PDF without text layer / DOCX / API+JSON) and update
  cadence. Download 1–2 representative sample files. Write a structured
  entry into `docs/source-inventory.md` (URL, format, cadence, notes).
- **Does not** write parser code or touch the database.

### `parser-dev`
- **Input:** sample file(s), target parser family, target canonical schema.
- **Job:** Implement or adjust a parser module for one parser family against
  the sample file(s), iterating until output rows validate against the
  canonical raw-row Pydantic schema. Writes a unit test fixture +  test.
- **Does not** do source discovery or scraping; assumes sample files already
  exist locally.

Both subagents are plain markdown agent definitions under `.claude/agents/`,
following the standard Claude Code subagent format (description, tools,
system prompt).

## 8. GitHub Hosting

- Repo created via `gh repo create planning-intelligence --private --source=. --remote=origin` once the initial scaffold + this spec are committed locally.
- Initial push of the scaffold to `main`.
- Collaborator addition is an owner-only action — done manually (see section
  9) rather than automated, since it grants access to private code and is not
  reversible without the collaborator noticing.

## 9. Manual Steps for the User (Collaborators)

After the initial push, to add a collaborator:

**Via GitHub CLI** (fastest):
```bash
gh repo add-collaborator planning-intelligence <github-username> --permission push
```
(`--permission` can be `pull`, `push`, `maintain`, `admin`, or `triage`.)

**Via GitHub web UI**:
1. Go to `https://github.com/<your-username>/planning-intelligence/settings/access`
2. Click "Add people"
3. Enter their GitHub username or email
4. Choose a role (Read / Triage / Write / Maintain / Admin)
5. They'll receive an invite email/notification to accept

## 10. Explicitly Deferred (Not in This Foundation)

- RAG/chat-based natural language Q&A (duffy's `chat_app.py` stack) — the dev
  plan's insight/update/detail services are plain SQL/PostGIS-backed, not
  RAG. Revisit as a separate later layer if still wanted.
- Any council beyond Galway (Limerick, Cork, Dublin, Waterford) — these get
  added one at a time via `/onboard-council` after the foundation lands.
- Market-derivation polygon data for Galway Metro commuter belt — needs the
  open questions from the 2026-06-25 commuter-shed discussion resolved first
  (commuter-belt membership rule, POWCAR data confirmation, partition vs.
  shared-belt approach). `src/markets/galway/metro.py` will scaffold as a
  stub pending that.
- CI/CD, deployment (Hetzner notes exist in duffy's README but aren't part of
  the foundation repo structure itself).
