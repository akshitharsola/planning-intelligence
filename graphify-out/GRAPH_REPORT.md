# Graph Report - planning-intelligence  (2026-11-04)

## Corpus Check
- 186 files · ~110,917 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 9, .example 1, .ini 1)

## Summary
- 1025 nodes · 2227 edges · 96 communities (35 shown, 61 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 141 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b21d9ab6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_matching_ladder.py
- normalize_row
- Application
- backfill_galway_city_chunked.py
- Ask Planning Intelligence Chat Feature
- answer_question
- DHLGH National Planning Dataset Design Spec
- BaseSource
- Base
- BaseModel
- search
- normalize_address
- normalize_dhlgh_row
- GalwayCityScraper
- DecisionDocument
- galway/decision_documents.py
- galway_city.py
- main.py
- CountyDocFetcher
- DHLGH National Planning Dataset — New Independent Source Design
- Foundation Design — Planning-Intelligence Platform
- County Stack Hardening Implementation Plan
- test_cleanup_stale_raw_files.py
- parse_notice
- test_ingest_decision_documents.py
- pipelines/decision_documents.py
- LLM hallucinated application_type value applied as hard filter (bug)
- Knowledge Graph (graphify-out)
- Discovery: Galway County publishes data via public ArcGIS Feature Service
- Decision reasons & conditions: design (DRAFT for approval)
- Value Proposition
- Risks and Mitigation Register
- test_decision_documents.py
- registry.py
- build_enrichment_plan
- open
- Web Dashboard v1 — Design
- Structured Location Data: What We Actually Have, and How to Pitch It
- open
- Market Need and Sizing (TAM/SAM/SOM)
- pre-commit
- Ingestion CLI Design — Galway City & County
- Task 7: Live ArcGIS Incremental-Run Acceptance Gate
- cleanup_after_test
- ApplicationEvent SQLAlchemy model
- Weekly Scheduled Ingestion + City PDF Staging & Retention Plan
- metro.py
- No-Merge/No-Write-to-applications Constraint
- Rationale: separate DHLGHApplicationCreate schema, not reuse of ApplicationCreate
- planning-intelligence
- Rationale: mark file ingested only if every row succeeded (self-healing retry)
- Migration 0003: add search indexes
- scripts/ingest_galway_city.py (run_city_ingestion)
- BaseSource ABC
- FastAPI app (src.web.main)
- GET /applications/{planning_authority}/{application_ref} route
- GET / dashboard route
- _replace_param Jinja2 filter
- Rationale: table rendered via partial so it can be swapped to HTMX/fetch later
- Rationale: charts are global, not filter-aware (v1 simplicity)
- Rationale: :path converter verified safe for slash-bearing application_ref
- Rationale: filter inputs are plain text, not dropdowns, in v1
- Rationale: only delete stale files confirmed ingested, never data loss

## God Nodes (most connected - your core abstractions)
1. `Application` - 37 edges
2. `parse_notice()` - 31 edges
3. `answer_question()` - 28 edges
4. `normalize_row()` - 26 edges
5. `MatchCandidate` - 25 edges
6. `DecisionDocument` - 25 edges
7. `normalize_county_row()` - 25 edges
8. `normalize_dhlgh_row()` - 23 edges
9. `ingest_application()` - 23 edges
10. `DHLGHApplication` - 22 edges

## Surprising Connections (you probably didn't know these)
- `Task 9: Chat wiring` --references--> `answer_question()`  [INFERRED]
  docs/superpowers/plans/2026-11-04-decision-reasons.md → src/services/chat_service.py
- `Task 8: Surface eircode and address in the UI` --references--> `Application`  [INFERRED]
  docs/superpowers/plans/2026-09-24-eircode-and-address-section.md → src/core/models/application.py
- `Task 1: Fix and verify the Eircode extraction regex` --references--> `extract_location()`  [INFERRED]
  docs/superpowers/plans/2026-09-24-eircode-and-address-section.md → src/core/normalization/location.py
- `Task 5: Backfill eircode for existing rows` --references--> `extract_eircode()`  [INFERRED]
  docs/superpowers/plans/2026-09-24-eircode-and-address-section.md → src/core/normalization/location.py
- `Task 2: Add `eircode` to the schema and ORM model` --references--> `ApplicationCreate`  [INFERRED]
  docs/superpowers/plans/2026-09-24-eircode-and-address-section.md → src/core/schemas/application.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **DHLGH cross-source identity matching ladder components** — matching_ladder_design, normalize_application_ref_design, normalize_address_design, ladder_matchcandidate, dhlgh_validation_pass_results [EXTRACTED 0.85]
- **DHLGH enrichment backfill implementation chain** — enrichment_backfill_design_spec, enrichment_backfill_plan, enrich_from_dhlgh_build_plan, enrich_from_dhlgh_apply_plan, drop_conflicting_targets, enrichment_backfill_live_run_results [EXTRACTED 0.90]
- **Council onboarding pipeline (source-onboarding -> classification -> scaffolding -> parser-dev)** — claude_skills_onboard_council_skill, claude_agents_source_onboarding_agent, claude_agents_parser_dev_agent, onboard_council_parser_family_classification [EXTRACTED 0.90]

## Communities (96 total, 61 thin omitted)

### Community 0 - "test_matching_ladder.py"
Cohesion: 0.14
Nodes (34): NamedTuple, MatchCandidate, MatchResult, Session, Last-resort fuzzy rung (spec section 9): matches here are surfaced for manual…, run_ladder(), rung1_ref_match(), rung2_address_match() (+26 more)

### Community 1 - "normalize_row"
Cohesion: 0.05
Nodes (68): File Structure, Task 1: Fix and verify the Eircode extraction regex, Task 2: Add `eircode` to the schema and ORM model, Task 3: Database migration to add the `eircode` column, Task 4: Wire eircode extraction into the normalization pipeline, Task 5: Backfill eircode for existing rows, pydantic, ApplicationEvent (+60 more)

### Community 2 - "Application"
Cohesion: 0.05
Nodes (57): alembic, get_database_url(), datetime, DeclarativeBase, dotenv, geoalchemy2, geoalchemy2_functions, logging (+49 more)

### Community 3 - "backfill_galway_city_chunked.py"
Cohesion: 0.05
Nodes (64): argparse, pathlib, main(), _match_source_type(), Chunked backfill runner for Galway City: processes the discovered PDF backlog…, run_batch(), main(), DHLGH ingestion CLI: discover -> normalize_dhlgh_row ->… (+56 more)

### Community 4 - "Ask Planning Intelligence Chat Feature"
Cohesion: 0.05
Nodes (45): Task 1: Reject Blank/Missing file_number, Task 2: Unrecognized source_type Fallback (STATUS_UNRECOGNIZED), DHLGH Cross-Source Identity Matching Ladder Plan, Friend-Hosted Ollama (LAN), OLLAMA_BASE_URL Config Switch, Jetson AGX Orin Ollama Hosting, OLLAMA_HOST=0.0.0.0 Binding, "AI Chat Is a Small Thing" - DB/Backend Priority Concern (+37 more)

### Community 5 - "answer_question"
Cohesion: 0.06
Nodes (62): Eircode and Address Section Implementation Plan, Global Constraints, Post-plan note: the Eircode Finder website, Review Focus, Task 7: Teach the chat assistant to recognize Eircode questions, json, os, Protocol (+54 more)

### Community 6 - "DHLGH National Planning Dataset Design Spec"
Cohesion: 0.07
Nodes (38): parser-dev Subagent, ApplicationCreate validation step, extract_planning_table interface signature, source-onboarding Subagent, docs/source-inventory.md entry, onboard-council Skill, DHLGH Galway source config, Galway City Council source config (+30 more)

### Community 10 - "search"
Cohesion: 0.30
Nodes (18): Task 6: Add `eircode` as a search filter, get_by_natural_key(), Session, search(), _cleanup(), _insert(), _seed(), test_get_by_natural_key_found() (+10 more)

### Community 11 - "normalize_address"
Cohesion: 0.12
Nodes (23): re, _find_matched_candidate(), Re-applies the same equality predicate the winning rung used, to recover which…, normalize_address(), normalize_address() — cross-source identity matching ladder rung 2 helper (spec…, normalize_application_ref(), normalize_application_ref() — cross-source identity matching ladder rung 1…, Returns the normalized ref string, or None (NORMALIZE_FAILED) if no known rule… (+15 more)

### Community 12 - "normalize_dhlgh_row"
Cohesion: 0.15
Nodes (22): _arcgis_date(), _clean_float(), _clean_str(), normalize_dhlgh_row(), DHLGH normalization maps the national ArcGIS Feature Service's `attributes`…, Converts an Esri JSON polygon (`{"rings": [[[x, y], ...], ...]}`) into EWKT…, DHLGH ArcGIS dates arrive as epoch milliseconds (unlike County's DD/MM/YYYY…, _rings_to_wkt() (+14 more)

### Community 13 - "GalwayCityScraper"
Cohesion: 0.06
Nodes (34): ABC, base64, requests, requests_adapters, BaseSource, Path, Return a list of dicts describing available remote items (e.g. PDF links), not…, Download the given items into self.temp_dir, return local paths. (+26 more)

### Community 14 - "DecisionDocument"
Cohesion: 0.30
Nodes (15): Task 2: Models and migration 0006, sqlalchemy_exc, DecisionDocument, DecisionItem, _cleanup(), cleanup_after_test(), fixture, test_delete_document_cascades_items() (+7 more)

### Community 15 - "galway/decision_documents.py"
Cohesion: 0.25
Nodes (7): dataclasses, http_cookiejar, fetch_eplanning_condition_count(), County document fetcher for Galway County Council decision notices and…, Convenience helper to fetch ePlanning condition count., urllib_error, urllib_request

### Community 16 - "galway_city.py"
Cohesion: 0.17
Nodes (20): pdfplumber, _clean_cells(), extract_planning_table(), _extract_rows(), _is_boilerplate(), _is_duplicate_header(), _looks_like_header(), _map_column() (+12 more)

### Community 17 - "main.py"
Cohesion: 0.06
Nodes (19): Task 8: Surface eircode and address in the UI, fastapi, fastapi_responses, fastapi_staticfiles, fastapi_templating, fastapi_testclient, get, post (+11 more)

### Community 18 - "CountyDocFetcher"
Cohesion: 0.15
Nodes (12): Any, main(), parse_args(), CLI script for ingesting decision documents and items for Galway County…, CountyDocFetcher, Fetch the HTML document list page for an application ref., Fetch PDF bytes for a DocLink. Returns None if body does not start with %PDF., Fetch condition count stated on ePlanning summary page. (+4 more)

### Community 19 - "DHLGH National Planning Dataset — New Independent Source Design"
Cohesion: 0.22
Nodes (9): Deterministic cross-source matching ladder (4 rungs), DHLGH National Planning Dataset — New Independent Source Design, normalize_address() canonical recipe, normalize_application_ref() helper, Rationale: DHLGH is additive, existing pipeline untouched, cheap to drop, Rationale: application_ref format varies unpredictably, no single transform rule, Risk: OBJECTID monotonicity is an unverified operational assumption, Application SQLAlchemy model (+1 more)

### Community 20 - "Foundation Design — Planning-Intelligence Platform"
Cohesion: 0.22
Nodes (9): Rationale: county-level grouping instead of flat authorities/ list, Rationale: PostgreSQL+PostGIS chosen over SQLite for real GIS queries, Rationale: raw downloads are a disposable buffer, not system of record, Foundation Design — Planning-Intelligence Platform, Planning-Intelligence Foundation Implementation Plan, /onboard-council skill, parser-dev subagent, source-onboarding subagent (+1 more)

### Community 21 - "County Stack Hardening Implementation Plan"
Cohesion: 0.33
Nodes (6): normalize_county_row coerces blank ApplicationNumber to empty string (bug), _derive_status silently defaults unrecognized decision to Received (bug), Missing indexes on filtered/sorted/ILIKE columns, County Stack Hardening Implementation Plan, Rationale: reject blank ApplicationNumber, natural key integrity, Rationale: fall into Unknown/Needs Review instead of silent Received

### Community 22 - "test_cleanup_stale_raw_files.py"
Cohesion: 0.26
Nodes (14): cleanup_stale_raw_files(), main(), _prune_empty_dirs(), Path, Deletes staged Galway City PDFs from data/galway/city/raw/ once they are older…, _make_file(), Path, test_deletes_ingested_file_older_than_30_days() (+6 more)

### Community 23 - "parse_notice"
Cohesion: 0.06
Nodes (55): collections, csv, Decision Reasons & Conditions Implementation Plan, Global Constraints, Parallel tracks (Antigravity, separate prompts; none block Phases 0–4), Parked by the user (2026-11-04), Phase 0 — Extractor, Phase 1 — Storage (+47 more)

### Community 24 - "test_ingest_decision_documents.py"
Cohesion: 0.24
Nodes (19): Task 4: Ingest CLI, ingest_application(), Fetch and ingest all decision notices for an application. Idempotent: skips…, DocLink, FakeCountyDocFetcher, date, read_spike_pdf(), _seed_app() (+11 more)

### Community 25 - "pipelines/decision_documents.py"
Cohesion: 0.14
Nodes (13): hashlib, random, get_stated_count(), Extract explicit condition/reason count stated on page 1 of County notices., extract_pdf_layout_text(), ingest_authority(), IngestResult, date (+5 more)

### Community 26 - "LLM hallucinated application_type value applied as hard filter (bug)"
Cohesion: 0.50
Nodes (4): LLM hallucinated application_type value applied as hard filter (bug), Chat Search Filter Bugs Implementation Plan, q filter does not match application_ref (bug), Rationale: validate application_type in code, not prompt wording alone

### Community 27 - "Knowledge Graph (graphify-out)"
Cohesion: 0.67
Nodes (4): graphify Repo Rules, Knowledge Graph (graphify-out), Pre-commit Hook (.githooks/pre-commit), Two-Person Team Git Workflow

### Community 28 - "Discovery: Galway County publishes data via public ArcGIS Feature Service"
Cohesion: 0.50
Nodes (4): Discovery: Galway County publishes data via public ArcGIS Feature Service, Real end-to-end smoke test (City + County, live data), Next Steps handoff notes (2026-06-28), Rationale: ArcGIS feed is strictly better than the original PDF plan

### Community 29 - "Decision reasons & conditions: design (DRAFT for approval)"
Cohesion: 0.13
Nodes (14): Anti-goals, Calls I made (change any), `decision_documents` (one row per downloaded notice), `decision_items` (one row per condition or refusal reason), Decision reasons & conditions: design (DRAFT for approval), Evidence it works (spike, offline), Extraction job (scope for the plan), Goals (+6 more)

### Community 30 - "Value Proposition"
Cohesion: 0.67
Nodes (3): Competitive Landscape (EirePlan, Precedent.ai), User Personas (Regulatory Planner, Developer/Architect), Value Proposition

### Community 31 - "Risks and Mitigation Register"
Cohesion: 0.67
Nodes (3): Legal and Regulatory Considerations (GDPR), Metrics and KPIs, Risks and Mitigation Register

### Community 32 - "test_decision_documents.py"
Cohesion: 0.11
Nodes (14): Phase 2 — Fetch and ingest (dry run), Task 3: County document fetcher, Task 5: Live dry run on 100 applications, list_decision_docs(), Parse document viewer HTML table and extract decision document links. Filters…, read_fixture(), test_condition_count_regex(), open() (+6 more)

### Community 33 - "registry.py"
Cohesion: 0.29
Nodes (8): is_galway_city(), is_galway_county(), derive_market_entities(), Market-entity derivation registry. Metro derivation is deliberately NOT wired…, FakeApplication, test_galway_city_council_maps_to_galway_city(), test_galway_county_council_maps_to_galway_county(), test_unknown_authority_maps_to_empty_list()

### Community 34 - "build_enrichment_plan"
Cohesion: 0.32
Nodes (11): build_enrichment_plan(), _drop_conflicting_targets(), Distinct DHLGH rows can each independently resolve to the same applications…, FakeApplication, FakeDHLGH, _make_session_with_rows(), test_ambiguous_match_produces_no_planned_update(), test_match_with_non_null_site_address_produces_no_planned_update_for_that_field() (+3 more)

### Community 36 - "Web Dashboard v1 — Design"
Cohesion: 0.67
Nodes (3): Rationale: prioritize credibility/provenance/speed over visual polish, Web Dashboard v1 — Design, Web Dashboard v1 Implementation Plan

### Community 37 - "Structured Location Data: What We Actually Have, and How to Pitch It"
Cohesion: 0.22
Nodes (8): 1. The Finding, in Plain Terms, 2. Current Coverage (Live Data, Verified), 3. Your Question: If We Have the Address, Why Can't We Convert It?, 4. What We Checked, and What It Costs, 5. Recommendation, 6. Vocabulary to Use From Now On, 7. The Pitch-Ready Paragraph, Structured Location Data: What We Actually Have, and How to Pitch It

### Community 43 - "cleanup_after_test"
Cohesion: 0.67
Nodes (3): _cleanup(), cleanup_after_test(), fixture

## Knowledge Gaps
- **111 isolated node(s):** `planning-intelligence`, `run_weekly_ingestion.sh script`, `start_stack.sh script`, `1. The Finding, in Plain Terms`, `2. Current Coverage (Live Data, Verified)` (+106 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 347 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **61 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CountyDocFetcher` connect `CountyDocFetcher` to `test_decision_documents.py`, `galway/decision_documents.py`, `parse_notice`, `test_ingest_decision_documents.py`, `pipelines/decision_documents.py`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `Logging configuration` connect `DHLGH National Planning Dataset Design Spec` to `Application`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `Application` (e.g. with `Task 8: Surface eircode and address in the UI` and `run_backfill()`) actually correct?**
  _`Application` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `parse_notice()` (e.g. with `Self-review notes` and `Task 1: Notice extractor (pure text → items)`) actually correct?**
  _`parse_notice()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `answer_question()` (e.g. with `Task 7: Teach the chat assistant to recognize Eircode questions` and `Task 9: Chat wiring`) actually correct?**
  _`answer_question()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `planning-intelligence`, `run_weekly_ingestion.sh script`, `start_stack.sh script` to the rest of the system?**
  _111 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_matching_ladder.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14453781512605043 - nodes in this community are weakly interconnected._