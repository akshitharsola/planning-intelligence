# Graph Report - /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/.claude/worktrees/web-dashboard  (2026-07-04)

## Corpus Check
- 90 files · ~73,497 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 336 nodes · 489 edges · 57 communities detected
- Extraction: 69% EXTRACTED · 31% INFERRED · 0% AMBIGUOUS · INFERRED: 150 edges (avg confidence: 0.76)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]

## God Nodes (most connected - your core abstractions)
1. `run_city_ingestion()` - 16 edges
2. `normalize_county_row()` - 16 edges
3. `run_county_ingestion()` - 14 edges
4. `GalwayCityScraper` - 12 edges
5. `normalize_row()` - 11 edges
6. `answer_question()` - 11 edges
7. `ApplicationCreate` - 10 edges
8. `GalwayCountyScraper` - 10 edges
9. `search()` - 10 edges
10. `_seed()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `test_is_file_ingested_false_when_unset()` --calls--> `is_file_ingested()`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/tests/unit/core/test_ingestion_state.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/core/ingestion_state.py
- `Galway City ingestion CLI: discover -> acquire -> parse -> normalize -> resolve` --uses--> `GalwayCityScraper`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/scripts/ingest_galway_city.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/sources/galway/city/scraper.py
- `Re-derive which pdf_patterns key matched this filename.      GalwayCityScraper.d` --uses--> `GalwayCityScraper`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/scripts/ingest_galway_city.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/sources/galway/city/scraper.py
- `Galway County ingestion CLI: discover -> normalize -> resolve -> publish against` --uses--> `GalwayCountyScraper`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/scripts/ingest_galway_county.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/sources/galway/county/scraper.py
- `chat_ask()` --calls--> `answer_question()`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/.claude/worktrees/web-dashboard/src/web/main.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/.claude/worktrees/web-dashboard/src/services/chat_service.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.11
Nodes (26): ApplicationCreate, ApplicationEventCreate, OtherRegulatoryFlags, BaseModel, _arcgis_date(), _clean_str(), _derive_status(), normalize_county_row() (+18 more)

### Community 1 - "Community 1"
Cohesion: 0.1
Nodes (19): ABC, BaseSource, _build_session(), GalwayCityScraper, GalwayCountyScraper, _make_dl_url(), _normalise_week(), _query_page() (+11 more)

### Community 2 - "Community 2"
Cohesion: 0.13
Nodes (20): answer_question(), _extract_filters(), _fallback_summary(), Natural-language Q&A over the applications table. Read-only: the LLM only extrac, Returns {"answer": str, "filters": dict, "applications": list, "total": int}., Returns {"answer": str, "filters": dict, "applications": list, "total": int}., Returns {"answer": str, "filters": dict, "applications": list, "total": int}., _summarize() (+12 more)

### Community 3 - "Community 3"
Cohesion: 0.14
Nodes (19): _extraction_prompt(), _today(), get_distinct_authorities(), get_monthly_counts(), get_status_breakdown(), get_summary(), get_type_breakdown(), chat_ask() (+11 more)

### Community 4 - "Community 4"
Cohesion: 0.15
Nodes (17): load_region_config(), Load a `config/<county>/<region>.yaml` region config file., main(), _match_source_type(), Galway City ingestion CLI: discover -> acquire -> parse -> normalize -> resolve, Re-derive which pdf_patterns key matched this filename.      GalwayCityScraper.d, run_city_ingestion(), is_file_ingested() (+9 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (14): Application, ApplicationEvent, Base, Base, DeclarativeBase, get_metrics_snapshot(), Minimal ingestion KPIs: rows ingested per run, per-region parser error counts/ra, record_ingestion_run() (+6 more)

### Community 6 - "Community 6"
Cohesion: 0.21
Nodes (16): main(), Galway County ingestion CLI: discover -> normalize -> resolve -> publish against, run_county_ingestion(), get_watermark(), set_watermark(), _cleanup(), _fake_records(), A mid-batch failure (OBJECTID 3002) must not block 3003 (a later,     successful (+8 more)

### Community 7 - "Community 7"
Cohesion: 0.2
Nodes (16): _clean_cells(), extract_planning_table(), _extract_rows(), _is_boilerplate(), _is_duplicate_header(), _looks_like_header(), _map_column(), _norm() (+8 more)

### Community 8 - "Community 8"
Cohesion: 0.16
Nodes (12): extract_json(), get_llm_client(), HostedApiClient, OllamaClient, Pluggable LLM backend for the chat feature. LLM_BACKEND env var selects the impl, OpenAI-compatible chat completions endpoint (opt-in via LLM_BACKEND=hosted_api)., Best-effort JSON extraction from a model reply that may include     surrounding, test_extract_json_invalid_returns_none() (+4 more)

### Community 9 - "Community 9"
Cohesion: 0.14
Nodes (3): _cleanup_detail(), _seed_detail(), test_detail_page_shows_all_expected_fields()

### Community 10 - "Community 10"
Cohesion: 0.31
Nodes (13): get_by_natural_key(), search(), application_detail(), _cleanup(), _insert(), _seed(), test_get_by_natural_key_found(), test_get_by_natural_key_not_found_returns_none() (+5 more)

### Community 11 - "Community 11"
Cohesion: 0.22
Nodes (8): is_galway_city(), is_galway_county(), derive_market_entities(), Market-entity derivation registry. Metro derivation is deliberately NOT wired in, FakeApplication, test_galway_city_council_maps_to_galway_city(), test_galway_county_council_maps_to_galway_county(), test_unknown_authority_maps_to_empty_list()

### Community 12 - "Community 12"
Cohesion: 0.31
Nodes (8): _extract_address(), _extract_area(), _extract_eircode(), extract_location(), _looks_like_address(), Location extraction for Galway descriptions — ported from duffy's location_extra, test_extract_location_finds_eircode_and_area(), test_extract_location_handles_empty_description()

### Community 13 - "Community 13"
Cohesion: 0.4
Nodes (2): create applications and events  Revision ID: 0001 Revises: Create Date: 2026-06-, # NOTE: a GIST spatial index on applications.site_geometry is created

### Community 14 - "Community 14"
Cohesion: 0.5
Nodes (0): 

### Community 15 - "Community 15"
Cohesion: 0.5
Nodes (1): create ingestion_state and ingested_files  Revision ID: 0002 Revises: 0001 Creat

### Community 16 - "Community 16"
Cohesion: 0.67
Nodes (0): 

### Community 17 - "Community 17"
Cohesion: 0.67
Nodes (0): 

### Community 18 - "Community 18"
Cohesion: 0.67
Nodes (1): # TODO: commuter-belt polygons pending — see docs/source-inventory.md and

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (0): 

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (0): 

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (0): 

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (0): 

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (0): 

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (0): 

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (0): 

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (0): 

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (0): 

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (0): 

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (0): 

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (0): 

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (0): 

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (0): 

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (0): 

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (0): 

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (0): 

### Community 42 - "Community 42"
Cohesion: 1.0
Nodes (0): 

### Community 43 - "Community 43"
Cohesion: 1.0
Nodes (0): 

### Community 44 - "Community 44"
Cohesion: 1.0
Nodes (0): 

### Community 45 - "Community 45"
Cohesion: 1.0
Nodes (0): 

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (0): 

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (0): 

### Community 48 - "Community 48"
Cohesion: 1.0
Nodes (0): 

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (0): 

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (0): 

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (0): 

### Community 52 - "Community 52"
Cohesion: 1.0
Nodes (0): 

### Community 53 - "Community 53"
Cohesion: 1.0
Nodes (1): Return a list of dicts describing available remote items         (e.g. PDF links

### Community 54 - "Community 54"
Cohesion: 1.0
Nodes (1): Download the given items into self.temp_dir, return local paths.

### Community 55 - "Community 55"
Cohesion: 1.0
Nodes (0): 

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **23 isolated node(s):** `A mid-batch failure (OBJECTID 3002) must not block 3003 (a later,     successful`, `Scripted client: returns queued replies in order, one per .chat() call.`, `Galway City weekly-list PDF parser — first concrete implementation of the pdf_ta`, `Open a PDF and extract all table rows as a list of dicts keyed by     column_map`, `Persisted incremental-ingestion state: County's OBJECTID watermark and City's pe` (+18 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 19`** (2 nodes): `get_database_url()`, `settings.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (2 nodes): `_reset_metrics_counters()`, `conftest.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (2 nodes): `test_application_has_natural_key_constraint()`, `test_application_natural_key.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (2 nodes): `main()`, `scaffold_tree.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (2 nodes): `renderBarChart()`, `app.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (1 nodes): `session.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `Return a list of dicts describing available remote items         (e.g. PDF links`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `Download the given items into self.temp_dir, return local paths.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `normalize_row()` connect `Community 0` to `Community 12`, `Community 4`, `Community 5`?**
  _High betweenness centrality (0.284) - this node is a cross-community bridge._
- **Why does `search()` connect `Community 10` to `Community 2`, `Community 3`, `Community 12`?**
  _High betweenness centrality (0.256) - this node is a cross-community bridge._
- **Why does `extract_location()` connect `Community 12` to `Community 0`?**
  _High betweenness centrality (0.252) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `run_city_ingestion()` (e.g. with `test_first_run_ingests_all_rows_and_marks_file()` and `test_second_run_skips_already_ingested_file()`) actually correct?**
  _`run_city_ingestion()` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `normalize_county_row()` (e.g. with `test_normalize_county_row_received()` and `test_normalize_county_row_granted()`) actually correct?**
  _`normalize_county_row()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `run_county_ingestion()` (e.g. with `test_first_run_ingests_all_and_sets_watermark()` and `test_second_run_with_stored_watermark_ingests_only_new()`) actually correct?**
  _`run_county_ingestion()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `GalwayCityScraper` (e.g. with `test_build_local_path_uses_temp_dir()` and `run_city_ingestion()`) actually correct?**
  _`GalwayCityScraper` has 5 INFERRED edges - model-reasoned connections that need verification._