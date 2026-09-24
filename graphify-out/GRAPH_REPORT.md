# Graph Report - planning-intelligence  (2026-09-24)

## Corpus Check
- 166 files · ~83,183 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 9, .example 1, .ini 1)

## Summary
- 778 nodes · 1238 edges · 116 communities (28 shown, 88 thin omitted)
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 270 edges (avg confidence: 0.76)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- test_matching_ladder.py
- normalize_county_row()
- enrich_from_dhlgh.py
- run_batch()
- Ask Planning Intelligence Chat Feature
- LLMClient
- DHLGH National Planning Dataset Design Spec
- run_dhlgh_ingestion()
- DHLGHApplication
- normalize_dhlgh_row()
- test_application_service.py
- test_chat_service.py
- resolve.py
- galway_city.py
- test_web_routes.py
- derive_market_entities()
- normalize_address()
- normalize_application_ref()
- run_county_ingestion()
- DHLGH National Planning Dataset — New Independent Source Des
- Foundation Design — Planning-Intelligence Platform
- County Stack Hardening Implementation Plan
- 0001_create_applications_and_events.py
- 0004_create_dhlgh_applications.py
- 0002_create_ingestion_state.py
- LLM hallucinated application_type value applied as hard filt
- Knowledge Graph (graphify-out)
- Discovery: Galway County publishes data via public ArcGIS Fe
- Value Proposition
- Risks and Mitigation Register
- metro.py
- Web Dashboard v1 — Design
- Market Need and Sizing (TAM/SAM/SOM)
- pre-commit
- Ingestion CLI Design — Galway City & County
- Task 7: Live ArcGIS Incremental-Run Acceptance Gate
- ApplicationEvent SQLAlchemy model
- Weekly Scheduled Ingestion + City PDF Staging & Retention Pl
- add search indexes  Revision ID: 0003 Revises: 0002 Create D
- Deletes staged Galway City PDFs from data/galway/city/raw/ o
- No-Merge/No-Write-to-applications Constraint
- Rationale: separate DHLGHApplicationCreate schema, not reuse
- Load a `config/<county>/<region>.yaml` region config file.
- County normalization maps Galway County Council's ArcGIS Fea
- ArcGIS dates here are DD/MM/YYYY strings; reject null-sentin
- ArcGIS dates here are DD/MM/YYYY strings; reject null-sentin
- Galway City ingestion CLI: discover -> acquire -> parse -> n
- Re-derive which pdf_patterns key matched this filename.     
- Rationale: mark file ingested only if every row succeeded (s
- Persisted incremental-ingestion state: County's OBJECTID wat
- Last-resort fuzzy rung (spec section 9): matches here are su
- Migration 0003: add search indexes
- Reject rows that don't look like real planning applications.
- scripts/ingest_galway_city.py (run_city_ingestion)
- Return a list of dicts describing available remote items    
- Download the given items into self.temp_dir, return local pa
- Interface every region's source module implements.
- BaseSource ABC
- FastAPI app (src.web.main)
- GET /applications/{planning_authority}/{application_ref} rou
- GET / dashboard route
- get_db() FastAPI dependency
- _replace_param Jinja2 filter
- Rationale: table rendered via partial so it can be swapped t
- Rationale: charts are global, not filter-aware (v1 simplicit
- Rationale: :path converter verified safe for slash-bearing a
- Rationale: filter inputs are plain text, not dropdowns, in v
- Rationale: only delete stale files confirmed ingested, never

## God Nodes (most connected - your core abstractions)
1. `normalize_county_row()` - 28 edges
2. `MatchCandidate` - 25 edges
3. `normalize_dhlgh_row()` - 18 edges
4. `build_enrichment_plan()` - 17 edges
5. `run_ladder()` - 17 edges
6. `FakeLLMClient` - 15 edges
7. `normalize_row()` - 15 edges
8. `LLMClient` - 15 edges
9. `normalize_row()` - 15 edges
10. `DHLGHApplication` - 14 edges

## Surprising Connections (you probably didn't know these)
- `Galway County Council source config` --semantically_similar_to--> `DHLGHScraper(BaseSource)`  [INFERRED] [semantically similar]
  config/galway/county.yaml → docs/superpowers/specs/2026-07-10-dhlgh-national-source-design.md
- `Application SQLAlchemy model` --conceptually_related_to--> `DHLGH National Planning Dataset — New Independent Source Design`  [INFERRED]
  src/core/models/application.py → docs/superpowers/specs/2026-07-10-dhlgh-national-source-design.md
- `test_is_file_ingested_false_when_unset()` --calls--> `is_file_ingested()`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/tests/unit/core/test_ingestion_state.py → src/core/ingestion_state.py
- `test_mark_then_is_file_ingested_roundtrips()` --calls--> `is_file_ingested()`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/tests/unit/core/test_ingestion_state.py → src/core/ingestion_state.py
- `test_normalize_county_row_received()` --calls--> `normalize_county_row()`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/.claude/worktrees/web-dashboard/tests/unit/pipelines/test_normalize_galway_county.py → src/core/normalization/galway_county.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Council onboarding pipeline (source-onboarding -> classification -> scaffolding -> parser-dev)** — claude_skills_onboard_council_skill, claude_agents_source_onboarding_agent, claude_agents_parser_dev_agent, onboard_council_parser_family_classification [EXTRACTED 0.90]
- **DHLGH cross-source identity matching ladder components** — matching_ladder_design, normalize_application_ref_design, normalize_address_design, ladder_matchcandidate, dhlgh_validation_pass_results [EXTRACTED 0.85]
- **DHLGH enrichment backfill implementation chain** — enrichment_backfill_design_spec, enrichment_backfill_plan, enrich_from_dhlgh_build_plan, enrich_from_dhlgh_apply_plan, drop_conflicting_targets, enrichment_backfill_live_run_results [EXTRACTED 0.90]

## Communities (116 total, 88 thin omitted)

### Community 0 - "test_matching_ladder.py"
Cohesion: 0.06
Nodes (72): geoalchemy2, geoalchemy2_functions, MatchResult, Cross-source identity matching ladder (spec section 9, docs/superpowers/specs/20, Last-resort fuzzy rung (spec section 9): matches here are surfaced     for manua, run_ladder(), rung1_ref_match(), rung2_address_match() (+64 more)

### Community 1 - "normalize_county_row()"
Cohesion: 0.06
Nodes (59): datetime, _expand_app_type(), _flag_yes(), normalize_row(), _parse_date(), Maps a raw parser row (dict, source-specific keys) into the canonical Applicatio, parametrize, pytest (+51 more)

### Community 2 - "enrich_from_dhlgh.py"
Cohesion: 0.08
Nodes (48): argparse, collections, _drop_conflicting_targets(), _find_matched_candidate(), DHLGH enrichment backfill (spec docs/superpowers/specs/2026-07-28-dhlgh-enrichme, Re-applies the same equality predicate the winning rung used, to     recover whi, MatchCandidate NamedTuple (extended with application_id), logging (+40 more)

### Community 3 - "run_batch()"
Cohesion: 0.06
Nodes (34): main(), _match_source_type(), Chunked backfill runner for Galway City: processes the discovered PDF backlog in, run_batch(), GalwayCityScraper, is_file_ingested(), load_region_config(), get_metrics_snapshot() (+26 more)

### Community 4 - "Ask Planning Intelligence Chat Feature"
Cohesion: 0.05
Nodes (45): Task 1: Reject Blank/Missing file_number, Task 2: Unrecognized source_type Fallback (STATUS_UNRECOGNIZED), DHLGH Cross-Source Identity Matching Ladder Plan, Friend-Hosted Ollama (LAN), OLLAMA_BASE_URL Config Switch, Jetson AGX Orin Ollama Hosting, OLLAMA_HOST=0.0.0.0 Binding, "AI Chat Is a Small Thing" - DB/Backend Priority Concern (+37 more)

### Community 5 - "LLMClient"
Cohesion: 0.06
Nodes (36): Natural-language Q&A over the applications table. Read-only: the LLM only extrac, Returns {"answer": str, "filters": dict, "applications": list, "total": int}., Returns {"answer": str, "filters": dict, "applications": list, "total": int}., Returns {"answer": str, "filters": dict, "applications": list, "total": int}., Returns {"answer": str, "filters": dict, "applications": list, "total": int}., Returns {"answer": str, "filters": dict, "applications": list, "total": int}., Returns {"answer": str, "filters": dict, "applications": list, "total": int}., Returns {"answer": str, "filters": dict, "applications": list, "total": int}. (+28 more)

### Community 6 - "DHLGH National Planning Dataset Design Spec"
Cohesion: 0.07
Nodes (37): parser-dev Subagent, ApplicationCreate validation step, extract_planning_table interface signature, source-onboarding Subagent, docs/source-inventory.md entry, onboard-council Skill, DHLGH Galway source config, Galway City Council source config (+29 more)

### Community 7 - "run_dhlgh_ingestion()"
Cohesion: 0.13
Nodes (24): BaseSource, main(), DHLGH ingestion CLI: discover -> normalize_dhlgh_row -> resolve_and_upsert_dhlgh, run_dhlgh_ingestion(), _build_session(), DHLGHScraper, _query_page(), Galway County Council planning register scraper — built fresh, no duffy preceden (+16 more)

### Community 8 - "DHLGHApplication"
Cohesion: 0.19
Nodes (22): Base, Base, DeclarativeBase, DHLGHApplication, apply_enrichment_plan(), build_enrichment_plan(), _base_application_kwargs(), _base_dhlgh_kwargs() (+14 more)

### Community 9 - "normalize_dhlgh_row()"
Cohesion: 0.13
Nodes (23): BaseModel, DHLGHApplicationCreate, _arcgis_date(), _clean_float(), _clean_str(), normalize_dhlgh_row(), DHLGH normalization maps the national ArcGIS Feature Service's `attributes` dict, Converts an Esri JSON polygon (`{"rings": [[[x, y], ...], ...]}`)     into EWKT (+15 more)

### Community 10 - "test_application_service.py"
Cohesion: 0.18
Nodes (22): _extract_address(), _extract_area(), _extract_eircode(), extract_location(), _looks_like_address(), Location extraction for Galway descriptions — ported from duffy's location_extra, application_service.get_by_natural_key(), application_service.search() (+14 more)

### Community 11 - "test_chat_service.py"
Cohesion: 0.32
Nodes (18): chat_service.answer_question(), _cleanup(), FakeLLMClient, RaisingLLMClient, Scripted client: returns queued replies in order, one per .chat() call., _seed(), test_answer_question_distinguishes_narrowed_filters_from_out_of_coverage(), test_answer_question_drops_authority_guessed_from_place_name_alone() (+10 more)

### Community 12 - "resolve.py"
Cohesion: 0.15
Nodes (18): Application, DHLGHApplication, DHLGHApplicationCreate, Resolve stage: dedup applications by the natural key (planning_authority + appli, src_core_models_application_event, src_core_schemas_application, src_core_schemas_dhlgh_application, ApplicationCreate (+10 more)

### Community 13 - "galway_city.py"
Cohesion: 0.18
Nodes (18): _clean_cells(), extract_planning_table(), _extract_rows(), _is_boilerplate(), _is_duplicate_header(), _looks_like_header(), _map_column(), _norm() (+10 more)

### Community 14 - "test_web_routes.py"
Cohesion: 0.14
Nodes (3): _cleanup_detail(), _seed_detail(), test_detail_page_shows_all_expected_fields()

### Community 15 - "derive_market_entities()"
Cohesion: 0.22
Nodes (8): is_galway_city(), is_galway_county(), derive_market_entities(), Market-entity derivation registry. Metro derivation is deliberately NOT wired in, FakeApplication, test_galway_city_council_maps_to_galway_city(), test_galway_county_council_maps_to_galway_county(), test_unknown_authority_maps_to_empty_list()

### Community 16 - "normalize_address()"
Cohesion: 0.27
Nodes (10): normalize_address(), normalize_address() — cross-source identity matching ladder rung 2 helper (spec, test_co_galway_variants_all_equivalent(), test_collapses_whitespace(), test_hyphenated_place_name_hyphen_preserved(), test_lowercases_and_strips_punctuation(), test_rd_and_st_abbreviations_expand(), test_standalone_galway_not_dropped_to_empty_string() (+2 more)

### Community 17 - "normalize_application_ref()"
Cohesion: 0.24
Nodes (10): normalize_application_ref(), normalize_application_ref() — cross-source identity matching ladder rung 1 helpe, Returns the normalized ref string, or None (NORMALIZE_FAILED) if no     known ru, Fixture table from spec section 9.1 (docs/superpowers/specs/2026-07-10-dhlgh-nat, test_already_normalized_city_ref_is_idempotent(), test_blank_input_cannot_normalize(), test_city_2660243_normalizes_to_slashed_form(), test_county_163_cannot_normalize() (+2 more)

### Community 18 - "run_county_ingestion()"
Cohesion: 0.35
Nodes (10): main(), Galway County ingestion CLI: discover -> normalize -> resolve -> publish against, run_county_ingestion(), _cleanup(), _fake_records(), A mid-batch failure (OBJECTID 3002) must not block 3003 (a later,     successful, test_dry_run_does_not_write_to_db_or_set_watermark(), test_first_run_ingests_all_and_sets_watermark() (+2 more)

### Community 19 - "DHLGH National Planning Dataset — New Independent Source Des"
Cohesion: 0.22
Nodes (9): Deterministic cross-source matching ladder (4 rungs), DHLGH National Planning Dataset — New Independent Source Design, normalize_address() canonical recipe, normalize_application_ref() helper, Rationale: DHLGH is additive, existing pipeline untouched, cheap to drop, Rationale: application_ref format varies unpredictably, no single transform rule, Risk: OBJECTID monotonicity is an unverified operational assumption, Application SQLAlchemy model (+1 more)

### Community 20 - "Foundation Design — Planning-Intelligence Platform"
Cohesion: 0.22
Nodes (9): Rationale: county-level grouping instead of flat authorities/ list, Rationale: PostgreSQL+PostGIS chosen over SQLite for real GIS queries, Rationale: raw downloads are a disposable buffer, not system of record, Foundation Design — Planning-Intelligence Platform, Planning-Intelligence Foundation Implementation Plan, /onboard-council skill, parser-dev subagent, source-onboarding subagent (+1 more)

### Community 21 - "County Stack Hardening Implementation Plan"
Cohesion: 0.33
Nodes (6): normalize_county_row coerces blank ApplicationNumber to empty string (bug), _derive_status silently defaults unrecognized decision to Received (bug), Missing indexes on filtered/sorted/ILIKE columns, County Stack Hardening Implementation Plan, Rationale: reject blank ApplicationNumber, natural key integrity, Rationale: fall into Unknown/Needs Review instead of silent Received

### Community 26 - "LLM hallucinated application_type value applied as hard filt"
Cohesion: 0.50
Nodes (4): LLM hallucinated application_type value applied as hard filter (bug), Chat Search Filter Bugs Implementation Plan, q filter does not match application_ref (bug), Rationale: validate application_type in code, not prompt wording alone

### Community 27 - "Knowledge Graph (graphify-out)"
Cohesion: 0.67
Nodes (4): graphify Repo Rules, Knowledge Graph (graphify-out), Pre-commit Hook (.githooks/pre-commit), Two-Person Team Git Workflow

### Community 28 - "Discovery: Galway County publishes data via public ArcGIS Fe"
Cohesion: 0.50
Nodes (4): Discovery: Galway County publishes data via public ArcGIS Feature Service, Real end-to-end smoke test (City + County, live data), Next Steps handoff notes (2026-06-28), Rationale: ArcGIS feed is strictly better than the original PDF plan

### Community 30 - "Value Proposition"
Cohesion: 0.67
Nodes (3): Competitive Landscape (EirePlan, Precedent.ai), User Personas (Regulatory Planner, Developer/Architect), Value Proposition

### Community 31 - "Risks and Mitigation Register"
Cohesion: 0.67
Nodes (3): Legal and Regulatory Considerations (GDPR), Metrics and KPIs, Risks and Mitigation Register

### Community 36 - "Web Dashboard v1 — Design"
Cohesion: 0.67
Nodes (3): Rationale: prioritize credibility/provenance/speed over visual polish, Web Dashboard v1 — Design, Web Dashboard v1 Implementation Plan

## Knowledge Gaps
- **80 isolated node(s):** `scripts/ingest_galway_city.py (run_city_ingestion)`, `ApplicationEvent SQLAlchemy model`, `ApplicationEventCreate Pydantic schema`, `ApplicationCreate Pydantic schema`, `Migration 0003: add search indexes` (+75 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 274 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **88 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `normalize_row()` connect `normalize_county_row()` to `test_application_service.py`, `run_batch()`?**
  _High betweenness centrality (0.148) - this node is a cross-community bridge._
- **Why does `extract_location()` connect `test_application_service.py` to `normalize_county_row()`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Why does `application_service.search()` connect `test_application_service.py` to `test_chat_service.py`?**
  _High betweenness centrality (0.122) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `normalize_county_row()` (e.g. with `run_county_ingestion()` and `_expand_app_type()`) actually correct?**
  _`normalize_county_row()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `normalize_dhlgh_row()` (e.g. with `DHLGHApplicationCreate` and `_parse_date()`) actually correct?**
  _`normalize_dhlgh_row()` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `scripts/ingest_galway_city.py (run_city_ingestion)`, `ApplicationEvent SQLAlchemy model`, `ApplicationEventCreate Pydantic schema` to the rest of the system?**
  _80 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_matching_ladder.py` be split into smaller, more focused modules?**
  _Cohesion score 0.061088485746019994 - nodes in this community are weakly interconnected._