# Foundation Development Plan – Planning-Intelligence Platform

## 1. Project Overview and Aim

This project is a planning‑intelligence platform for Ireland, starting with Galway and expanding to other councils. The core aim is to:

- Aggregate planning applications across multiple planning authorities (city + county).
- Normalize and store them in a consistent schema.
- Provide three product layers per region:
  - `CITY` (e.g. GALWAY_CITY)
  - `METRO / COMMUTER BELT` (e.g. GALWAY_METRO)
  - `COUNTY` (e.g. GALWAY_COUNTY)
- Expose insights, updates, and detailed views for planners, developers, and other stakeholders.

The existing Galway City work is the initial technical proof: weekly‑list PDFs parsed into structured fields with a normalization mapping.

The goal now is to design a generalizable foundation that supports many councils and source formats, aligned with the product and business thinking in your strategy report.

---

## 2. Scope and Layers (City, Metro, County)

### 2.1 Source Entities vs Market Entities

We distinguish between:

- **Source entities** (ingestion units)  
  Example: `GALWAY_CITY_COUNCIL`, `GALWAY_COUNTY_COUNCIL`, `DUBLIN_CITY_COCO`, `CORK_CITY_COCO`.

- **Market entities** (user-facing regions)  
  Example: `GALWAY_CITY`, `GALWAY_METRO`, `GALWAY_COUNTY`, `DUBLIN_METRO`, etc.

A single market entity can draw data from one or more source entities plus geospatial rules. For example:

- `GALWAY_CITY` → primarily Galway City Council applications (inside city boundary).
- `GALWAY_METRO` → Galway City + selected commuter towns from Galway County (e.g. Oranmore, Tuam) using county datasets + spatial filters.
- `GALWAY_COUNTY` → all Galway County Council applications regardless of commuter status.

This separation allows you to scale across Ireland and still present intuitive regions to users.

---

## 3. Data Sources by Authority (Galway Example)

### 3.1 Galway City

Primary sources:

- Weekly planning list PDFs from GCC Planning Files repository (`files.galwaycity.ie/gccplanninglists/#/`). These contain tabular fields like:
  - `FILE NUMBER`
  - `APPLICANTS NAME`
  - `APP. TYPE`
  - `DATE RECEIVED`
  - `DEVELOPMENT DESCRIPTION AND LOCATION`
  - flags/decision fields such as `EIS RECD.`, `PROT. STRU`, `IPC LIC.`, `WASTE LIC.`, `M.O. DATE`, `M.O. NUMBER`.

Characteristics:

- Multiple report types (Received, Granted, Refused, Invalid, Further Info) with shared core columns and report‑specific tails.
- No explicit detail URLs; status and some flags are implicit or scattered.

### 3.2 Galway County

Primary sources:

- Weekly planning lists page: links to PDFs for applications received, granted, refused, on hold (further information), appealed and decided.
- ePlanning listing: `SearchListing/RECEIVED` etc. with listing types (Applications Received, Decisions Due, Decisions Made) and a rolling 7–42 day window for recent data.
- Planning files search / documents viewer: search by ref number or location, then view documents and details.
- Open data / map viewer: ArcGIS “Planning Applications registered after 2015 / 1995–2015” datasets and public planning viewer.

Characteristics:

- Good for historical backfill via weekly PDFs, plus near‑real‑time updates via the ePlanning listings.
- Rich geospatial context through open data for commuting and metro areas.

### 3.3 Other Councils (Preview)

From your multi‑city comparison:

- **Limerick** — similar ruled‑table PDFs to Galway City; almost no extra work beyond filename patterns.
- **Cork** — similar PDFs, with some column naming differences and one problematic report needing text‑mode extraction.
- **Dublin** — `.docx` weekly lists with paragraph-based records, needs a paragraph/state‑machine parser.
- **Waterford** — PDF with no text layer, requires OCR first.

These inform parser families and architecture.

---

## 4. Canonical Data Model

We generalize to a canonical schema that every parser should target.

### 4.1 Application Core

- `id` (internal UUID)
- `planning_authority` (e.g. "Galway City Council", "Galway County Council")
- `source_entity` (e.g. `GALWAY_CITY_COUNCIL`)
- `application_ref`
- `application_ref_type` (string / enum; some councils might have multiple ref schemes)
- `applicant_name`
- `site_address`
- `site_locality` (town/village; derivable from address or geodata)
- `site_county`
- `site_geometry` (optional; point/polygon from GIS datasets)
- `development_description`
- `application_type` (normalized: Permission, Retention, Outline, etc.)

### 4.2 Lifecycle and Status

- `planning_status_current` (high‑level: Received, Further Info, Granted, Refused, Withdrawn, Appealed, Decided, Invalid)
- `status_event_type` (event for this record instance, e.g. APPLICATION_RECEIVED, DECISION_GRANTED)
- `date_received`
- `decision_due_date` (computed from statutory rules when not present)
- `decision_date`
- `further_information_flag`
- `protected_structure_flag`
- `eia_eis_flag` (EIS/EIA required/received)
- `other_regulatory_flags` (e.g. IPC licence, Waste licence) in a structured subdocument.

### 4.3 Provenance and URLs

- `official_detail_url` (planning search/detail page if available; e.g. ePlanning ref URL).
- `official_documents_url` (document viewer entry or direct file listing; optional).
- `source_system` (e.g. "Galway City Weekly Lists PDF", "Galway County ePlanning listing").
- `source_file` (filename or URL for raw file; one per ingestion run).
- `source_ingested_at`
- `raw_payload_json` (original parsed row/fields as JSON blob, including authority‑specific flags).

### 4.4 Market-Layer Fields

- `market_entity` (e.g. GALWAY_CITY, GALWAY_METRO, GALWAY_COUNTY)
- `commuter_belt_flag` (boolean or categorical, derived from locality and metro rules)

---

## 5. Lifecycle Model: Events vs Current State

To support insight, update, and detail modes we store both events and current state.

### 5.1 Tables

- `applications` – one row per application, latest known state.
- `application_events` – one row per event per application.

Example events:

- APPLICATION_RECEIVED (from Received weekly list or ePlanning Received).
- FURTHER_INFORMATION_REQUESTED / RECEIVED (from FI weekly lists).
- DECISION_GRANTED / DECISION_REFUSED (from Granted/Refused lists).
- APPLICATION_WITHDRAWN.
- APPEAL_LODGED / APPEAL_DECIDED (from county weekly lists + An Bord Pleanála weekly lists).

Update mode queries events since last run. Insight mode aggregates events over time. Detail mode shows the event history for a single application.

---

## 6. Ingestion Pipeline

For each source entity (e.g. Galway City, Galway County), implement a pipeline with these stages.

### 6.1 Discover

- Identify new or updated source items:
  - New weekly PDFs on city/county sites.
  - New ePlanning listings within the last N days.
  - New open data snapshots or GIS layers.

### 6.2 Acquire

- Download PDFs/DOCX.
- Fetch listing pages (HTML/JSON).
- Record `source_file` and metadata, hash for deduplication.

### 6.3 Extract (Parser Families)

Use parser families based on source type:

- `pdf_table_lines` – ruled table PDFs with text layer (Galway City, Limerick, most Cork).
- `pdf_table_text_fallback` – for Cork invalid‑applications where header row splits under lines mode.
- `docx_state_machine` – for Dublin `.docx` weekly lists with paragraphs and section headers.
- `pdf_ocr_pipeline` – for Waterford and any scanned PDFs; renders to images, runs OCR, then structured parsing.

Output a normalized "raw row" object per record plus document‑level metadata.

### 6.4 Normalize

- Map each raw row into the canonical schema:
  - Direct mappings like FILE NUMBER → `application_ref`.
  - Code lookups (P/R/O → Permission/Retention/Outline, etc.).
  - Split combined fields like `DEVELOPMENT DESCRIPTION AND LOCATION` into address vs description using heuristics and geocoding.
- Attach `source_system`, `source_entity`, `source_file`, and `raw_payload_json`.

### 6.5 Resolve + Lifecycle Update

- Use `planning_authority + application_ref` as natural key to link multiple rows for the same application.
- Generate `application_events` from input context (which report/listing it came from).
- Update `applications` current state based on new events.

### 6.6 Market Derivation

- Use `planning_authority`, `site_geometry` / locality, and rules to assign each application to one or more `market_entity` values.
  - If authority is Galway City and location inside city boundary → `GALWAY_CITY`.
  - If location in defined commuter belt polygon → also `GALWAY_METRO`.
  - All Galway County applications → `GALWAY_COUNTY`.

---

## 7. Repo / Folder Structure

A repo layout matching the architecture:

```text
planning-intelligence/
├── README.md
├── pyproject.toml
├── docs/
│   ├── foundation-development-plan.md   # this document
│   ├── source-inventory.md             # per council sources & URLs
│   ├── schema.md                       # canonical schema description
│   └── market-layering.md              # city/metro/county rules
├── config/
│   ├── settings.py
│   ├── logging.yaml
│   └── authorities/
│       ├── galway_city.yaml
│       ├── galway_county.yaml
│       ├── dublin_city.yaml
│       └── cork_city.yaml
├── data/
│   ├── raw/
│   │   ├── galway_city/
│   │   ├── galway_county/
│   │   ├── dublin_city/
│   │   └── cork_city/
│   ├── staged/
│   └── exports/
├── src/
│   ├── core/
│   │   ├── models/        # SQLAlchemy/Pydantic models
│   │   ├── db/            # DB session, migrations
│   │   ├── schemas/       # canonical schema definitions
│   │   ├── normalization/
│   │   ├── lifecycle/
│   │   └── geo/
│   ├── parsers/
│   │   ├── pdf_lines/
│   │   ├── pdf_text_fallback/
│   │   ├── docx_state_machine/
│   │   └── pdf_ocr/
│   ├── sources/
│   │   ├── base/
│   │   ├── galway_city/
│   │   ├── galway_county/
│   │   ├── dublin_city/
│   │   └── cork_city/
│   ├── pipelines/
│   │   ├── discover.py
│   │   ├── acquire.py
│   │   ├── extract.py
│   │   ├── normalize.py
│   │   ├── resolve.py
│   │   └── publish.py
│   ├── markets/
│   │   ├── registry.py
│   │   ├── galway_city.py
│   │   ├── galway_metro.py
│   │   └── galway_county.py
│   └── services/
│       ├── search_service.py
│       ├── update_service.py
│       └── insight_service.py
└── tests/
    ├── fixtures/
    ├── unit/
    ├── integration/
    └── regression/
```

This layout makes it easy to add new authorities and markets over time while keeping core logic reusable.

---

## 8. Services and Interfaces

To support the three modes (insight, update, detail) define:

### 8.1 Search Service

- Query `applications` by ref, site, authority, or market entity.
- Used by developer/planner UI.

### 8.2 Update Service

- "What changed since date X?" based on `application_events`.
- Feeds email reports or dashboard panels.

### 8.3 Insight Service

- Aggregates counts/trends: applications per area, status distribution, time to decision, commuter‑belt hotspots.

Each service calls into standardized repositories (`applications`, `application_events`) and uses market definitions to scope queries.

---

## 9. Connection to Business and Aim

The business/strategy report frames the product around:

- Clear problem statements: too much manual aggregation across councils.
- Personas: planners and developers needing faster, unified views.
- Value proposition: "save hours/week, avoid missed deadlines, get cross‑council insight."
- Technical feasibility: multi‑parser ingestion + GIS data.
- Roadmap: Galway‑first pilot, then scale to all councils.

This development foundation:

- Implements multi‑council ingestion in a modular way (sources + parsers).
- Supports personas via the three modes (insight, update, detail).
- Enables city/metro/county layers that match how users think about markets.
- Sets up for scaling to 31 local authorities and eventually AI/insight layers.

Together with the strategy report, this document tells advisors and collaborators: "here’s the product we want to build, and here’s how we plan to build it."