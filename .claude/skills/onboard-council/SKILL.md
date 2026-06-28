---
name: onboard-council
description: Onboards a new council/region into the planning-intelligence platform — research, parser classification, scaffolding, and a working parser draft for human review. Invoke as /onboard-council <county_slug> <region_slug>, e.g. /onboard-council cork city.
---

# Onboard Council

Scaffolds source acquisition and parsing for one new council/region. Galway
City and County were built directly during the platform's foundation pass,
not through this skill — this skill is for every council added afterward.

This skill does **not** run the ingestion pipeline end-to-end and does
**not** write to the database. It only scaffolds code and config for human
review per step 6 below.

## Steps

1. **Check for existing config.** Look for `config/<county_slug>/<region_slug>.yaml`.
   If it already exists, treat this invocation as an update/resume: read the
   existing file and skip straight to step 5 with the parser family it
   already records, unless the user asked specifically to re-research the
   source.

2. **Dispatch `source-onboarding`.** Give it the county/region slug and any
   council name context available. It researches the region's planning-list
   site(s), determines file format and update cadence, downloads 1-2 sample
   files into `data/<county_slug>/<region_slug>/temp/samples/`, and appends
   findings to `docs/source-inventory.md`.

3. **Classify the parser family** from the subagent's findings:
   - `pdf_table_lines` — PDF with a text layer, tabular/columnar rows (the
     family both Galway City and Galway County use).
   - `pdf_table_text_fallback` — PDF with a text layer but inconsistent
     table structure, needing line-by-line heuristics instead of fixed
     columns.
   - `docx_state_machine` — Word documents, needs a stateful line-by-line
     parser.
   - `pdf_ocr_pipeline` — PDF with no text layer (scanned/image-only),
     needs OCR before any text extraction.

4. **Scaffold config and source module.**
   - Create `config/<county_slug>/<region_slug>.yaml` following the shape
     used by `config/galway/city.yaml` and `config/galway/county.yaml`:
     `source_entity`, `planning_authority`, `parser_family`, source URL(s),
     and `pdf_patterns` (or the equivalent filename/identification patterns
     for the chosen format).
   - Create `src/sources/<county_slug>/<region_slug>/` with a thin module
     implementing `src.sources.base.source.BaseSource` (`discover() ->
     list[dict]`, `acquire(items: list[dict]) -> list[Path]`), following the
     pattern in `src/sources/galway/city/scraper.py` or
     `src/sources/galway/county/scraper.py`.

5. **Dispatch `parser-dev`** with the sample file paths and the chosen
   parser family. It builds or adjusts
   `src/parsers/<family>/<county_slug>_<region_slug>.py` and a unit test
   under `tests/unit/parsers/`, iterating until the test passes against the
   real sample file(s).

6. **Report back to the human**, covering:
   - What was scaffolded (config path, source module path, parser path).
   - Parser test status (pass/fail, row count from sample file).
   - What needs human review before this goes further — e.g. ambiguous
     column mappings parser-dev flagged, market-derivation rules for the
     new region (does it belong to an existing market entity or need a new
     one in `src/markets/registry.py`?), and whether the source-onboarding
     subagent's cadence/format determination should be spot-checked against
     the live site.
