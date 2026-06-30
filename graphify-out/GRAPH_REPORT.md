# Graph Report - /Users/akshitharsola/Documents/AiAgentic/planning-intelligence  (2026-06-30)

## Corpus Check
- 67 files · ~43,388 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 186 nodes · 217 edges · 48 communities detected
- Extraction: 72% EXTRACTED · 28% INFERRED · 0% AMBIGUOUS · INFERRED: 60 edges (avg confidence: 0.73)
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

## God Nodes (most connected - your core abstractions)
1. `normalize_county_row()` - 12 edges
2. `ApplicationCreate` - 10 edges
3. `normalize_row()` - 10 edges
4. `GalwayCityScraper` - 9 edges
5. `GalwayCountyScraper` - 8 edges
6. `extract_location()` - 7 edges
7. `OtherRegulatoryFlags` - 7 edges
8. `BaseSource` - 7 edges
9. `_normalise_rows()` - 6 edges
10. `derive_market_entities()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `test_map_column_exact_match()` --calls--> `_map_column()`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/tests/unit/parsers/test_galway_city_pdf_lines.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/parsers/pdf_lines/galway_city.py
- `test_map_column_partial_match()` --calls--> `_map_column()`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/tests/unit/parsers/test_galway_city_pdf_lines.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/parsers/pdf_lines/galway_city.py
- `test_map_column_fallback_slug()` --calls--> `_map_column()`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/tests/unit/parsers/test_galway_city_pdf_lines.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/parsers/pdf_lines/galway_city.py
- `test_normalise_rows_skips_boilerplate()` --calls--> `_normalise_rows()`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/tests/unit/parsers/test_galway_city_pdf_lines.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/parsers/pdf_lines/galway_city.py
- `test_application_create_requires_natural_key()` --calls--> `ApplicationCreate`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/tests/unit/core/test_application_schema.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/core/schemas/application.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.15
Nodes (20): ApplicationCreate, OtherRegulatoryFlags, _arcgis_date(), _clean_str(), _derive_status(), normalize_county_row(), County normalization reuses City's status/event mapping and date parsing (both a, ArcGIS dates here are DD/MM/YYYY strings; reject null-sentinel values. (+12 more)

### Community 1 - "Community 1"
Cohesion: 0.16
Nodes (13): ABC, BaseSource, _build_session(), GalwayCountyScraper, _query_page(), acquire(), BaseSource, discover() (+5 more)

### Community 2 - "Community 2"
Cohesion: 0.2
Nodes (16): _clean_cells(), extract_planning_table(), _extract_rows(), _is_boilerplate(), _is_duplicate_header(), _looks_like_header(), _map_column(), _norm() (+8 more)

### Community 3 - "Community 3"
Cohesion: 0.22
Nodes (8): is_galway_city(), is_galway_county(), derive_market_entities(), Market-entity derivation registry. Metro derivation is deliberately NOT wired in, FakeApplication, test_galway_city_council_maps_to_galway_city(), test_galway_county_council_maps_to_galway_county(), test_unknown_authority_maps_to_empty_list()

### Community 4 - "Community 4"
Cohesion: 0.26
Nodes (6): GalwayCityScraper, _make_dl_url(), _normalise_week(), Galway City Council weekly planning lists scraper.  Ported from duffy's scraper., test_build_local_path_uses_temp_dir(), test_normalise_week_handles_dot_date_ranges()

### Community 5 - "Community 5"
Cohesion: 0.21
Nodes (8): Application, ApplicationEvent, Base, Base, DeclarativeBase, Resolve stage: dedup applications by the natural key (planning_authority + appli, resolve_and_upsert(), test_normalize_resolve_publish_roundtrip()

### Community 6 - "Community 6"
Cohesion: 0.31
Nodes (8): _extract_address(), _extract_area(), _extract_eircode(), extract_location(), _looks_like_address(), Location extraction for Galway descriptions — ported from duffy's location_extra, test_extract_location_finds_eircode_and_area(), test_extract_location_handles_empty_description()

### Community 7 - "Community 7"
Cohesion: 0.25
Nodes (6): get_metrics_snapshot(), Minimal ingestion KPIs: rows ingested per run, per-region parser error counts/ra, record_ingestion_run(), publish(), Publish stage: commits the session and records ingestion metrics (spec section 3, test_record_ingestion_run_increments_counters()

### Community 8 - "Community 8"
Cohesion: 0.4
Nodes (3): ApplicationEventCreate, BaseModel, test_application_event_create()

### Community 9 - "Community 9"
Cohesion: 0.4
Nodes (3): load_region_config(), Load a `config/<county>/<region>.yaml` region config file., test_load_galway_city_config()

### Community 10 - "Community 10"
Cohesion: 0.4
Nodes (2): create applications and events  Revision ID: 0001 Revises: Create Date: 2026-06-, # NOTE: a GIST spatial index on applications.site_geometry is created

### Community 11 - "Community 11"
Cohesion: 0.5
Nodes (0): 

### Community 12 - "Community 12"
Cohesion: 0.67
Nodes (0): 

### Community 13 - "Community 13"
Cohesion: 0.67
Nodes (0): 

### Community 14 - "Community 14"
Cohesion: 0.67
Nodes (1): # TODO: commuter-belt polygons pending — see docs/source-inventory.md and

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (0): 

### Community 16 - "Community 16"
Cohesion: 1.0
Nodes (0): 

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
Nodes (1): Return a list of dicts describing available remote items         (e.g. PDF links

### Community 45 - "Community 45"
Cohesion: 1.0
Nodes (1): Download the given items into self.temp_dir, return local paths.

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (0): 

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **13 isolated node(s):** `Galway City weekly-list PDF parser — first concrete implementation of the pdf_ta`, `Open a PDF and extract all table rows as a list of dicts keyed by     column_map`, `Location extraction for Galway descriptions — ported from duffy's location_extra`, `create applications and events  Revision ID: 0001 Revises: Create Date: 2026-06-`, `# NOTE: a GIST spatial index on applications.site_geometry is created` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 15`** (2 nodes): `get_database_url()`, `settings.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (2 nodes): `_reset_metrics_counters()`, `conftest.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (2 nodes): `test_application_has_natural_key_constraint()`, `test_application_natural_key.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (2 nodes): `main()`, `scaffold_tree.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (1 nodes): `__init__.py`
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
- **Thin community `Community 34`** (1 nodes): `session.py`
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
- **Thin community `Community 44`** (1 nodes): `Return a list of dicts describing available remote items         (e.g. PDF links`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (1 nodes): `Download the given items into self.temp_dir, return local paths.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `normalize_row()` connect `Community 0` to `Community 5`, `Community 6`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `ApplicationCreate` connect `Community 0` to `Community 8`, `Community 5`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `test_normalize_resolve_publish_roundtrip()` connect `Community 5` to `Community 0`, `Community 7`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `normalize_county_row()` (e.g. with `test_normalize_county_row_received()` and `test_normalize_county_row_granted()`) actually correct?**
  _`normalize_county_row()` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `ApplicationCreate` (e.g. with `County normalization reuses City's status/event mapping and date parsing (both a` and `ArcGIS dates here are DD/MM/YYYY strings; reject null-sentinel values.`) actually correct?**
  _`ApplicationCreate` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `normalize_row()` (e.g. with `test_normalize_row_received_maps_to_application_received_event()` and `test_normalize_row_granted_sets_decision_fields()`) actually correct?**
  _`normalize_row()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `GalwayCityScraper` (e.g. with `BaseSource` and `test_build_local_path_uses_temp_dir()`) actually correct?**
  _`GalwayCityScraper` has 2 INFERRED edges - model-reasoned connections that need verification._