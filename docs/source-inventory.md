# Source Inventory

Per-council/region planning data sources: URLs, file formats, update cadence.
Populated incrementally — Galway City and County entries added in Task 6/9;
every council after that is appended by the `/onboard-council` skill's
`source-onboarding` subagent.

## Galway City

(added in Task 6)

## Galway County

- **Weekly-list page** (`config.galway.county.weekly_list_url`): plain HTML,
  PDF download links, scraped with `src/sources/galway/county/scraper.py`.
  URL needs confirmation by `source-onboarding` subagent before relying on
  it in production — placeholder per spec section 5.2.
- **ePlanning listing** (`config.galway.county.eplanning_endpoint`):
  `SearchListing/RECEIVED` etc., rolling 7-42 day window. Captured in config
  for future use; not yet implemented as an acquirer in this foundation pass.
- **ArcGIS open-data layers**: historical/geospatial backfill, referenced in
  dev-plan section 3.2. Not yet implemented.
- **Parser family**: `pdf_table_lines`, same family as Galway City pending
  confirmation against real sample PDFs (dev-plan section 3.2's "rich
  geospatial context" note implies similar tabular structure, but this is
  an assumption to verify, not a guarantee).
