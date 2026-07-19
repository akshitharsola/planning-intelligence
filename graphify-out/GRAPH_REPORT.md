# Graph Report - /Users/akshitharsola/Documents/AiAgentic/planning-intelligence  (2026-07-19)

## Corpus Check
- 112 files · ~104,163 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 483 nodes · 799 edges · 66 communities detected
- Extraction: 65% EXTRACTED · 35% INFERRED · 0% AMBIGUOUS · INFERRED: 280 edges (avg confidence: 0.74)
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
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]

## God Nodes (most connected - your core abstractions)
1. `answer_question()` - 19 edges
2. `run_city_ingestion()` - 18 edges
3. `normalize_county_row()` - 18 edges
4. `normalize_dhlgh_row()` - 18 edges
5. `normalize_row()` - 18 edges
6. `LLMClient` - 17 edges
7. `FakeLLMClient` - 15 edges
8. `ApplicationCreate` - 15 edges
9. `run_dhlgh_ingestion()` - 14 edges
10. `run_county_ingestion()` - 14 edges

## Surprising Connections (you probably didn't know these)
- `test_is_file_ingested_false_when_unset()` --calls--> `is_file_ingested()`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/tests/unit/core/test_ingestion_state.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/core/ingestion_state.py
- `DHLGH ingestion CLI: discover -> normalize_dhlgh_row -> resolve_and_upsert_dhlgh` --uses--> `DHLGHScraper`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/scripts/ingest_dhlgh.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/sources/dhlgh/scraper.py
- `Galway County ingestion CLI: discover -> normalize -> resolve -> publish against` --uses--> `GalwayCountyScraper`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/scripts/ingest_galway_county.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/sources/galway/county/scraper.py
- `chat_ask()` --calls--> `answer_question()`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/.claude/worktrees/web-dashboard/src/web/main.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/services/chat_service.py
- `Natural-language Q&A over the applications table. Read-only: the LLM only extrac` --uses--> `LLMClient`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/.claude/worktrees/web-dashboard/src/services/chat_service.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/.claude/worktrees/web-dashboard/src/services/llm_client.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.08
Nodes (39): ApplicationCreate, ApplicationEventCreate, OtherRegulatoryFlags, BaseModel, _arcgis_date(), _clean_str(), _derive_status(), normalize_county_row() (+31 more)

### Community 1 - "Community 1"
Cohesion: 0.1
Nodes (26): main(), _match_source_type(), Chunked backfill runner for Galway City: processes the discovered PDF backlog in, run_batch(), load_region_config(), Load a `config/<county>/<region>.yaml` region config file., main(), _match_source_type() (+18 more)

### Community 2 - "Community 2"
Cohesion: 0.1
Nodes (27): _contains_application_ref(), _extract_filters(), _extraction_prompt(), _first_day_last_month(), _is_valid_iso_date(), _last_day_last_month(), _mentions_authority(), Natural-language Q&A over the applications table. Read-only: the LLM only extrac (+19 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (27): Returns {"answer": str, "filters": dict, "applications": list, "total": int}., Returns {"answer": str, "filters": dict, "applications": list, "total": int}., Returns {"answer": str, "filters": dict, "applications": list, "total": int}., Returns {"answer": str, "filters": dict, "applications": list, "total": int}., Returns {"answer": str, "filters": dict, "applications": list, "total": int}., Returns {"answer": str, "filters": dict, "applications": list, "total": int}., Returns {"answer": str, "filters": dict, "applications": list, "total": int}., Returns {"answer": str, "filters": dict, "applications": list, "total": int}. (+19 more)

### Community 4 - "Community 4"
Cohesion: 0.13
Nodes (26): main(), DHLGH ingestion CLI: discover -> normalize_dhlgh_row -> resolve_and_upsert_dhlgh, run_dhlgh_ingestion(), main(), Galway County ingestion CLI: discover -> normalize -> resolve -> publish against, run_county_ingestion(), get_watermark(), Persisted incremental-ingestion state: County's OBJECTID watermark and City's pe (+18 more)

### Community 5 - "Community 5"
Cohesion: 0.13
Nodes (21): ABC, BaseSource, _build_session(), DHLGHScraper, GalwayCountyScraper, _query_page(), Galway City Council weekly planning lists scraper.  Ported from duffy's scraper., acquire() (+13 more)

### Community 6 - "Community 6"
Cohesion: 0.1
Nodes (20): Application, ApplicationEvent, Base, Base, DeclarativeBase, DHLGHApplication, get_metrics_snapshot(), Minimal ingestion KPIs: rows ingested per run, per-region parser error counts/ra (+12 more)

### Community 7 - "Community 7"
Cohesion: 0.16
Nodes (23): get_by_natural_key(), search(), _extract_address(), _extract_area(), _extract_eircode(), extract_location(), _looks_like_address(), Location extraction for Galway descriptions — ported from duffy's location_extra (+15 more)

### Community 8 - "Community 8"
Cohesion: 0.27
Nodes (19): answer_question(), Returns {"answer": str, "filters": dict, "applications": list, "total": int}., _cleanup(), FakeLLMClient, RaisingLLMClient, Scripted client: returns queued replies in order, one per .chat() call., _seed(), test_answer_question_distinguishes_narrowed_filters_from_out_of_coverage() (+11 more)

### Community 9 - "Community 9"
Cohesion: 0.18
Nodes (18): _clean_cells(), extract_planning_table(), _extract_rows(), _is_boilerplate(), _is_duplicate_header(), _looks_like_header(), _map_column(), _norm() (+10 more)

### Community 10 - "Community 10"
Cohesion: 0.18
Nodes (17): DHLGHApplicationCreate, _arcgis_date(), _clean_float(), _clean_str(), normalize_dhlgh_row(), DHLGH normalization maps the national ArcGIS Feature Service's `attributes` dict, Converts an Esri JSON polygon (`{"rings": [[[x, y], ...], ...]}`)     into EWKT, DHLGH ArcGIS dates arrive as epoch milliseconds (unlike County's     DD/MM/YYYY (+9 more)

### Community 11 - "Community 11"
Cohesion: 0.14
Nodes (3): _cleanup_detail(), _seed_detail(), test_detail_page_shows_all_expected_fields()

### Community 12 - "Community 12"
Cohesion: 0.31
Nodes (11): cleanup_stale_raw_files(), main(), _prune_empty_dirs(), Deletes staged Galway City PDFs from data/galway/city/raw/ once they are older t, _make_file(), test_deletes_ingested_file_older_than_30_days(), test_does_not_delete_file_younger_than_30_days(), test_does_not_delete_stale_file_that_was_never_ingested() (+3 more)

### Community 13 - "Community 13"
Cohesion: 0.22
Nodes (8): is_galway_city(), is_galway_county(), derive_market_entities(), Market-entity derivation registry. Metro derivation is deliberately NOT wired in, FakeApplication, test_galway_city_council_maps_to_galway_city(), test_galway_county_council_maps_to_galway_county(), test_unknown_authority_maps_to_empty_list()

### Community 14 - "Community 14"
Cohesion: 0.27
Nodes (10): normalize_address(), normalize_address() — cross-source identity matching ladder rung 2 helper (spec, test_co_galway_variants_all_equivalent(), test_collapses_whitespace(), test_hyphenated_place_name_hyphen_preserved(), test_lowercases_and_strips_punctuation(), test_rd_and_st_abbreviations_expand(), test_standalone_galway_not_dropped_to_empty_string() (+2 more)

### Community 15 - "Community 15"
Cohesion: 0.24
Nodes (10): normalize_application_ref(), normalize_application_ref() — cross-source identity matching ladder rung 1 helpe, Returns the normalized ref string, or None (NORMALIZE_FAILED) if no     known ru, Fixture table from spec section 9.1 (docs/superpowers/specs/2026-07-10-dhlgh-nat, test_already_normalized_city_ref_is_idempotent(), test_blank_input_cannot_normalize(), test_city_2660243_normalizes_to_slashed_form(), test_county_163_cannot_normalize() (+2 more)

### Community 16 - "Community 16"
Cohesion: 0.4
Nodes (0): 

### Community 17 - "Community 17"
Cohesion: 0.4
Nodes (2): create applications and events  Revision ID: 0001 Revises: Create Date: 2026-06-, # NOTE: a GIST spatial index on applications.site_geometry is created

### Community 18 - "Community 18"
Cohesion: 0.4
Nodes (2): create dhlgh_applications  Revision ID: 0004 Revises: 0003 Create Date: 2026-07-, # NOTE: a GIST spatial index on dhlgh_applications.site_geometry is

### Community 19 - "Community 19"
Cohesion: 0.5
Nodes (0): 

### Community 20 - "Community 20"
Cohesion: 0.5
Nodes (1): add search indexes  Revision ID: 0003 Revises: 0002 Create Date: 2026-07-04 00:0

### Community 21 - "Community 21"
Cohesion: 0.5
Nodes (1): create ingestion_state and ingested_files  Revision ID: 0002 Revises: 0001 Creat

### Community 22 - "Community 22"
Cohesion: 0.67
Nodes (0): 

### Community 23 - "Community 23"
Cohesion: 0.67
Nodes (1): # TODO: commuter-belt polygons pending — see docs/source-inventory.md and

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
Nodes (0): 

### Community 54 - "Community 54"
Cohesion: 1.0
Nodes (0): 

### Community 55 - "Community 55"
Cohesion: 1.0
Nodes (0): 

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (0): 

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (0): 

### Community 58 - "Community 58"
Cohesion: 1.0
Nodes (0): 

### Community 59 - "Community 59"
Cohesion: 1.0
Nodes (0): 

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (0): 

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (0): 

### Community 62 - "Community 62"
Cohesion: 1.0
Nodes (1): Return a list of dicts describing available remote items         (e.g. PDF links

### Community 63 - "Community 63"
Cohesion: 1.0
Nodes (1): Download the given items into self.temp_dir, return local paths.

### Community 64 - "Community 64"
Cohesion: 1.0
Nodes (0): 

### Community 65 - "Community 65"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **41 isolated node(s):** `Fixture table from spec section 9.1 (docs/superpowers/specs/2026-07-10-dhlgh-nat`, `A mid-batch failure (OBJECTID 3002) must not block 3003 (a later,     successful`, `Scripted client: returns queued replies in order, one per .chat() call.`, `Deletes staged Galway City PDFs from data/galway/city/raw/ once they are older t`, `Galway City weekly-list PDF parser — first concrete implementation of the pdf_ta` (+36 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 24`** (2 nodes): `get_database_url()`, `settings.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (2 nodes): `_reset_metrics_counters()`, `conftest.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (2 nodes): `test_application_has_natural_key_constraint()`, `test_application_natural_key.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (2 nodes): `main()`, `scaffold_tree.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (2 nodes): `renderBarChart()`, `app.js`
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
- **Thin community `Community 42`** (1 nodes): `__init__.py`
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
- **Thin community `Community 50`** (1 nodes): `session.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 62`** (1 nodes): `Return a list of dicts describing available remote items         (e.g. PDF links`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (1 nodes): `Download the given items into self.temp_dir, return local paths.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 64`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `normalize_row()` connect `Community 0` to `Community 1`, `Community 6`, `Community 7`?**
  _High betweenness centrality (0.278) - this node is a cross-community bridge._
- **Why does `search()` connect `Community 7` to `Community 8`, `Community 2`?**
  _High betweenness centrality (0.239) - this node is a cross-community bridge._
- **Why does `extract_location()` connect `Community 7` to `Community 0`?**
  _High betweenness centrality (0.238) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `answer_question()` (e.g. with `test_answer_question_extracts_filters_and_summarizes()` and `test_answer_question_unfiltered_search_when_llm_extracts_no_filters()`) actually correct?**
  _`answer_question()` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `run_city_ingestion()` (e.g. with `test_first_run_ingests_all_rows_and_marks_file()` and `test_second_run_skips_already_ingested_file()`) actually correct?**
  _`run_city_ingestion()` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `normalize_county_row()` (e.g. with `test_normalize_county_row_received()` and `test_normalize_county_row_granted()`) actually correct?**
  _`normalize_county_row()` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `normalize_dhlgh_row()` (e.g. with `test_normalize_dhlgh_row_basic_fields()` and `test_normalize_dhlgh_row_empty_postcode_is_not_an_error()`) actually correct?**
  _`normalize_dhlgh_row()` has 13 INFERRED edges - model-reasoned connections that need verification._