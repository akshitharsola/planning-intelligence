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
- Porting the Galway City source from duffy
- A custom Claude Code skill (`/onboard-council`) for the recurring
  "add a new council" workflow
- Two subagents (`source-onboarding`, `parser-dev`) that the skill dispatches to
- GitHub hosting and collaborator setup

Out of scope for this foundation: the chat/RAG layer (`chat_app.py`,
`rag_engine.py`, `embedder.py` in duffy), insight/update/detail service UIs,
and any council beyond Galway City. These are explicitly deferred — see
section 7.

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

Follows `docs/foundation-development-plan.md` section 7 layout exactly, with
two additions: `.claude/` for the project-scoped skill and subagents, and
`docker-compose.yml` for local Postgres+PostGIS.

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
│   └── authorities/
│       └── galway_city.yaml
├── data/
│   ├── raw/galway_city/
│   ├── staged/
│   └── exports/
├── src/
│   ├── core/{models,db,schemas,normalization,lifecycle,geo}/
│   ├── parsers/{pdf_lines,pdf_text_fallback,docx_state_machine,pdf_ocr}/
│   ├── sources/{base,galway_city}/
│   ├── pipelines/{discover,acquire,extract,normalize,resolve,publish}.py
│   ├── markets/{registry,galway_city,galway_metro,galway_county}.py
│   └── services/{search_service,update_service,insight_service}.py
└── tests/{fixtures,unit,integration,regression}/
```

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

## 5. Porting Galway City from Duffy

Duffy's existing working code becomes the first concrete `sources/galway_city`
implementation:

| Duffy file | New home | Adaptation needed |
|---|---|---|
| `scraper.py` | `src/sources/galway_city/scraper.py` | Same scraping logic; output path goes to `data/raw/galway_city/` instead of duffy's ad-hoc dirs. |
| `pdf_extractor.py` | `src/parsers/pdf_lines/galway_city.py` | Becomes the first concrete implementation of the `pdf_table_lines` parser family interface. |
| `data_processor.py` | Split across `src/pipelines/normalize.py` + `src/core/normalization/` | Row-mapping logic (FILE NUMBER → `application_ref`, etc.) becomes the canonical normalization mapping for Galway City. |
| `database.py` | `src/core/db/` | Re-targeted from SQLite ad-hoc tables to the canonical Postgres schema. |
| `folder_walker.py`, `config.py` | Reference only | Logic folded into `config/authorities/galway_city.yaml` + `src/pipelines/discover.py`. |
| `chat_app.py`, `rag_engine.py`, `embedder.py`, `query_engine.py`, `report_generator.py` | **Not ported** | Out of scope — see section 7. |

The original `duffy-main-repo-main` directory is left untouched as a reference;
nothing is deleted from it.

## 6. Custom Skill: `/onboard-council`

Project-scoped skill at `.claude/skills/onboard-council/SKILL.md`. Invoked as
`/onboard-council <council_slug>` (e.g. `/onboard-council galway_county`).

Workflow:

1. Check if `config/authorities/<council>.yaml` already exists — if so, treat
   as an update/resume rather than a fresh onboarding.
2. Dispatch the **`source-onboarding`** subagent to research the council's
   planning-list site(s): URL(s), file format, update cadence, and to pull
   down 1–2 sample files into `data/raw/<council>/samples/`. Findings get
   appended to `docs/source-inventory.md`.
3. Based on the subagent's findings, classify the parser family:
   `pdf_table_lines`, `pdf_table_text_fallback`, `docx_state_machine`, or
   `pdf_ocr_pipeline` (per dev plan section 6.3 and duffy's
   `multi_city_comparison.md` precedent).
4. Scaffold `config/authorities/<council>.yaml` (source URLs, parser family,
   filename patterns) and `src/sources/<council>/` (thin source module
   following the `src/sources/base/` interface).
5. Dispatch the **`parser-dev`** subagent with the sample files and chosen
   parser family to build/iterate the parser under
   `src/parsers/<family>/<council>.py`, with a unit test in
   `tests/unit/parsers/` that asserts the sample file extracts into valid
   canonical raw rows.
6. Report back: what was scaffolded, parser test status, and what still needs
   human review (e.g. ambiguous column mappings, market-derivation rules for
   the new council).

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
- Any council beyond Galway City (County, Limerick, Cork, Dublin, Waterford)
  — these get added one at a time via `/onboard-council` after the foundation
  lands.
- Market-derivation polygon data for Galway Metro commuter belt — needs the
  open questions from the 2026-06-25 commuter-shed discussion resolved first
  (commuter-belt membership rule, POWCAR data confirmation, partition vs.
  shared-belt approach). `src/markets/galway_metro.py` will scaffold as a
  stub pending that.
- CI/CD, deployment (Hetzner notes exist in duffy's README but aren't part of
  the foundation repo structure itself).
