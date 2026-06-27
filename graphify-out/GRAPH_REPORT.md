# Graph Report - /Users/akshitharsola/Documents/AiAgentic/planning-intelligence  (2026-06-27)

## Corpus Check
- 45 files · ~30,541 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 91 nodes · 65 edges · 40 communities detected
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.69)
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

## God Nodes (most connected - your core abstractions)
1. `GalwayCityScraper` - 9 edges
2. `BaseSource` - 6 edges
3. `ApplicationCreate` - 4 edges
4. `Base` - 4 edges
5. `test_build_local_path_uses_temp_dir()` - 3 edges
6. `ApplicationEvent` - 3 edges
7. `Application` - 3 edges
8. `ApplicationEventCreate` - 3 edges
9. `load_region_config()` - 3 edges
10. `_normalise_week()` - 3 edges

## Surprising Connections (you probably didn't know these)
- `Galway City Council weekly planning lists scraper.  Ported from duffy's scraper.` --uses--> `BaseSource`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/sources/galway/city/scraper.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/sources/base/source.py
- `GalwayCityScraper` --uses--> `BaseSource`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/sources/galway/city/scraper.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/sources/base/source.py
- `test_application_create_requires_natural_key()` --calls--> `ApplicationCreate`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/tests/unit/core/test_application_schema.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/core/schemas/application.py
- `test_application_create_rejects_missing_application_ref()` --calls--> `ApplicationCreate`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/tests/unit/core/test_application_schema.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/core/schemas/application.py
- `test_application_event_create()` --calls--> `ApplicationEventCreate`  [INFERRED]
  /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/tests/unit/core/test_application_event_schema.py → /Users/akshitharsola/Documents/AiAgentic/planning-intelligence/src/core/schemas/application_event.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.23
Nodes (7): BaseSource, GalwayCityScraper, _make_dl_url(), _normalise_week(), Galway City Council weekly planning lists scraper.  Ported from duffy's scraper., test_build_local_path_uses_temp_dir(), test_normalise_week_handles_dot_date_ranges()

### Community 1 - "Community 1"
Cohesion: 0.22
Nodes (7): ApplicationCreate, ApplicationEventCreate, OtherRegulatoryFlags, BaseModel, test_application_event_create(), test_application_create_rejects_missing_application_ref(), test_application_create_requires_natural_key()

### Community 2 - "Community 2"
Cohesion: 0.29
Nodes (5): Application, ApplicationEvent, Base, Base, DeclarativeBase

### Community 3 - "Community 3"
Cohesion: 0.33
Nodes (3): ABC, BaseSource, Interface every region's source module implements.

### Community 4 - "Community 4"
Cohesion: 0.4
Nodes (2): create applications and events  Revision ID: 0001 Revises: Create Date: 2026-06-, # NOTE: a GIST spatial index on applications.site_geometry is created

### Community 5 - "Community 5"
Cohesion: 0.4
Nodes (3): load_region_config(), Load a `config/<county>/<region>.yaml` region config file., test_load_galway_city_config()

### Community 6 - "Community 6"
Cohesion: 0.67
Nodes (0): 

### Community 7 - "Community 7"
Cohesion: 0.67
Nodes (0): 

### Community 8 - "Community 8"
Cohesion: 1.0
Nodes (0): 

### Community 9 - "Community 9"
Cohesion: 1.0
Nodes (0): 

### Community 10 - "Community 10"
Cohesion: 1.0
Nodes (0): 

### Community 11 - "Community 11"
Cohesion: 1.0
Nodes (0): 

### Community 12 - "Community 12"
Cohesion: 1.0
Nodes (0): 

### Community 13 - "Community 13"
Cohesion: 1.0
Nodes (0): 

### Community 14 - "Community 14"
Cohesion: 1.0
Nodes (0): 

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
Nodes (1): Return a list of dicts describing available remote items         (e.g. PDF links

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (1): Download the given items into self.temp_dir, return local paths.

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (0): 

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **6 isolated node(s):** `create applications and events  Revision ID: 0001 Revises: Create Date: 2026-06-`, `# NOTE: a GIST spatial index on applications.site_geometry is created`, `Load a `config/<county>/<region>.yaml` region config file.`, `Interface every region's source module implements.`, `Return a list of dicts describing available remote items         (e.g. PDF links` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 8`** (2 nodes): `get_database_url()`, `settings.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 9`** (2 nodes): `test_application_has_natural_key_constraint()`, `test_application_natural_key.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 10`** (2 nodes): `main()`, `scaffold_tree.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 11`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 12`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 13`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 14`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 15`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (1 nodes): `__init__.py`
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
- **Thin community `Community 26`** (1 nodes): `session.py`
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
- **Thin community `Community 36`** (1 nodes): `Return a list of dicts describing available remote items         (e.g. PDF links`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (1 nodes): `Download the given items into self.temp_dir, return local paths.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GalwayCityScraper` connect `Community 0` to `Community 3`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Why does `BaseSource` connect `Community 3` to `Community 0`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `GalwayCityScraper` (e.g. with `BaseSource` and `test_build_local_path_uses_temp_dir()`) actually correct?**
  _`GalwayCityScraper` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `BaseSource` (e.g. with `GalwayCityScraper` and `Galway City Council weekly planning lists scraper.  Ported from duffy's scraper.`) actually correct?**
  _`BaseSource` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `ApplicationCreate` (e.g. with `test_application_create_requires_natural_key()` and `test_application_create_rejects_missing_application_ref()`) actually correct?**
  _`ApplicationCreate` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `Base` (e.g. with `ApplicationEvent` and `Application`) actually correct?**
  _`Base` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `test_build_local_path_uses_temp_dir()` (e.g. with `GalwayCityScraper` and `._build_local_path()`) actually correct?**
  _`test_build_local_path_uses_temp_dir()` has 2 INFERRED edges - model-reasoned connections that need verification._