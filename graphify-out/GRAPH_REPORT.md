# Graph Report - /Users/akshitharsola/Documents/AiAgentic/planning-intelligence  (2026-07-02)

## Corpus Check
- 76 files · ~61,617 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 232 nodes · 316 edges · 52 communities detected
- Extraction: 66% EXTRACTED · 34% INFERRED · 0% AMBIGUOUS · INFERRED: 108 edges (avg confidence: 0.75)
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

## God Nodes (most connected - your core abstractions)
1. `run_city_ingestion()` - 17 edges
2. `run_county_ingestion()` - 14 edges
3. `normalize_county_row()` - 13 edges
4. `GalwayCityScraper` - 12 edges
5. `ApplicationCreate` - 11 edges
6. `normalize_row()` - 11 edges
7. `GalwayCountyScraper` - 10 edges
8. `OtherRegulatoryFlags` - 8 edges
9. `_normalise_rows()` - 7 edges
10. `get_watermark()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `test_is_file_ingested_false_when_unset()` --calls--> `is_file_ingested()`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/tests/unit/core/test_ingestion_state.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/core/ingestion_state.py
- `Galway City ingestion CLI: discover -> acquire -> parse -> normalize -> resolve` --uses--> `GalwayCityScraper`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/scripts/ingest_galway_city.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/sources/galway/city/scraper.py
- `Re-derive which pdf_patterns key matched this filename.      GalwayCityScraper.d` --uses--> `GalwayCityScraper`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/scripts/ingest_galway_city.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/sources/galway/city/scraper.py
- `Galway County ingestion CLI: discover -> normalize -> resolve -> publish against` --uses--> `GalwayCountyScraper`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/scripts/ingest_galway_county.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/sources/galway/county/scraper.py
- `test_map_column_exact_match()` --calls--> `_map_column()`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/tests/unit/parsers/test_galway_city_pdf_lines.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/parsers/pdf_lines/galway_city.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.13
Nodes (23): ApplicationCreate, OtherRegulatoryFlags, BaseModel, _arcgis_date(), _clean_str(), _derive_status(), normalize_county_row(), County normalization reuses City's status/event mapping and date parsing (both a (+15 more)

### Community 1 - "Community 1"
Cohesion: 0.15
Nodes (17): load_region_config(), Load a `config/<county>/<region>.yaml` region config file., main(), _match_source_type(), Galway City ingestion CLI: discover -> acquire -> parse -> normalize -> resolve, Re-derive which pdf_patterns key matched this filename.      GalwayCityScraper.d, run_city_ingestion(), is_file_ingested() (+9 more)

### Community 2 - "Community 2"
Cohesion: 0.18
Nodes (18): _clean_cells(), extract_planning_table(), _extract_rows(), _is_boilerplate(), _is_duplicate_header(), _looks_like_header(), _map_column(), _norm() (+10 more)

### Community 3 - "Community 3"
Cohesion: 0.21
Nodes (16): main(), Galway County ingestion CLI: discover -> normalize -> resolve -> publish against, run_county_ingestion(), get_watermark(), set_watermark(), _cleanup(), _fake_records(), A mid-batch failure (OBJECTID 3002) must not block 3003 (a later,     successful (+8 more)

### Community 4 - "Community 4"
Cohesion: 0.16
Nodes (13): ABC, BaseSource, _build_session(), GalwayCountyScraper, _query_page(), acquire(), BaseSource, discover() (+5 more)

### Community 5 - "Community 5"
Cohesion: 0.22
Nodes (8): is_galway_city(), is_galway_county(), derive_market_entities(), Market-entity derivation registry. Metro derivation is deliberately NOT wired in, FakeApplication, test_galway_city_council_maps_to_galway_city(), test_galway_county_council_maps_to_galway_county(), test_unknown_authority_maps_to_empty_list()

### Community 6 - "Community 6"
Cohesion: 0.21
Nodes (8): Application, ApplicationEvent, Base, Base, DeclarativeBase, Resolve stage: dedup applications by the natural key (planning_authority + appli, resolve_and_upsert(), test_normalize_resolve_publish_roundtrip()

### Community 7 - "Community 7"
Cohesion: 0.26
Nodes (6): GalwayCityScraper, _make_dl_url(), _normalise_week(), Galway City Council weekly planning lists scraper.  Ported from duffy's scraper., test_build_local_path_uses_temp_dir(), test_normalise_week_handles_dot_date_ranges()

### Community 8 - "Community 8"
Cohesion: 0.31
Nodes (8): _extract_address(), _extract_area(), _extract_eircode(), extract_location(), _looks_like_address(), Location extraction for Galway descriptions — ported from duffy's location_extra, test_extract_location_finds_eircode_and_area(), test_extract_location_handles_empty_description()

### Community 9 - "Community 9"
Cohesion: 0.25
Nodes (6): get_metrics_snapshot(), Minimal ingestion KPIs: rows ingested per run, per-region parser error counts/ra, record_ingestion_run(), publish(), Publish stage: commits the session and records ingestion metrics (spec section 3, test_record_ingestion_run_increments_counters()

### Community 10 - "Community 10"
Cohesion: 0.4
Nodes (2): create applications and events  Revision ID: 0001 Revises: Create Date: 2026-06-, # NOTE: a GIST spatial index on applications.site_geometry is created

### Community 11 - "Community 11"
Cohesion: 0.5
Nodes (0): 

### Community 12 - "Community 12"
Cohesion: 0.5
Nodes (2): ApplicationEventCreate, test_application_event_create()

### Community 13 - "Community 13"
Cohesion: 0.5
Nodes (1): create ingestion_state and ingested_files  Revision ID: 0002 Revises: 0001 Creat

### Community 14 - "Community 14"
Cohesion: 0.67
Nodes (0): 

### Community 15 - "Community 15"
Cohesion: 0.67
Nodes (0): 

### Community 16 - "Community 16"
Cohesion: 0.67
Nodes (1): # TODO: commuter-belt polygons pending — see docs/source-inventory.md and

### Community 17 - "Community 17"
Cohesion: 1.0
Nodes (0): 

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (0): 

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
Nodes (1): Return a list of dicts describing available remote items         (e.g. PDF links

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (1): Download the given items into self.temp_dir, return local paths.

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (0): 

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **16 isolated node(s):** `A mid-batch failure (OBJECTID 3002) must not block 3003 (a later,     successful`, `Galway City weekly-list PDF parser — first concrete implementation of the pdf_ta`, `Open a PDF and extract all table rows as a list of dicts keyed by     column_map`, `Persisted incremental-ingestion state: County's OBJECTID watermark and City's pe`, `Location extraction for Galway descriptions — ported from duffy's location_extra` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 17`** (2 nodes): `get_database_url()`, `settings.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (2 nodes): `_reset_metrics_counters()`, `conftest.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (2 nodes): `test_application_has_natural_key_constraint()`, `test_application_natural_key.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (2 nodes): `main()`, `scaffold_tree.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (1 nodes): `__init__.py`
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
- **Thin community `Community 38`** (1 nodes): `session.py`
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
- **Thin community `Community 48`** (1 nodes): `Return a list of dicts describing available remote items         (e.g. PDF links`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (1 nodes): `Download the given items into self.temp_dir, return local paths.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run_city_ingestion()` connect `Community 1` to `Community 0`, `Community 2`, `Community 4`, `Community 6`, `Community 7`, `Community 9`?**
  _High betweenness centrality (0.248) - this node is a cross-community bridge._
- **Why does `run_county_ingestion()` connect `Community 3` to `Community 0`, `Community 1`, `Community 4`, `Community 6`, `Community 9`?**
  _High betweenness centrality (0.141) - this node is a cross-community bridge._
- **Why does `normalize_row()` connect `Community 0` to `Community 8`, `Community 1`, `Community 6`?**
  _High betweenness centrality (0.128) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `run_city_ingestion()` (e.g. with `test_first_run_ingests_all_rows_and_marks_file()` and `test_second_run_skips_already_ingested_file()`) actually correct?**
  _`run_city_ingestion()` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `run_county_ingestion()` (e.g. with `test_first_run_ingests_all_and_sets_watermark()` and `test_second_run_with_stored_watermark_ingests_only_new()`) actually correct?**
  _`run_county_ingestion()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `normalize_county_row()` (e.g. with `test_normalize_county_row_received()` and `test_normalize_county_row_granted()`) actually correct?**
  _`normalize_county_row()` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `GalwayCityScraper` (e.g. with `Galway City ingestion CLI: discover -> acquire -> parse -> normalize -> resolve` and `Re-derive which pdf_patterns key matched this filename.      GalwayCityScraper.d`) actually correct?**
  _`GalwayCityScraper` has 5 INFERRED edges - model-reasoned connections that need verification._