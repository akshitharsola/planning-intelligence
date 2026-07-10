# Context

I'm building a planning-application intelligence database for Ireland, currently covering
Galway City Council and Galway County Council. Data comes from two official sources:

1. **Galway County Council** — published via an ArcGIS FeatureServer/REST feed. Each record
   has a free-text `Location` field (e.g. "Shanbally , Craughwell ,") with NO dedicated
   postal code / Eircode field. Only ~0.4% of ~20,375 records happen to have an Eircode
   incidentally typed into the free-text location by whoever entered the data.

2. **Galway City Council** — published as weekly PDF planning lists (tables scraped from
   PDF). Each record has a `description` field combining development description AND
   address as one free-text blob (e.g. "...construction of a new dwelling...3 Park Avenue
   Salthill Galway H91XN5H"), again with no dedicated address or Eircode column. About
   ~50% of ~527 City records happen to have a real Eircode embedded in that free text
   (verified genuine, e.g. "H91 RKR9", "H91XN5H" — valid Galway Eircode routing keys),
   but it is NOT a structured, reliable field — it's incidental to whether the applicant's
   description happened to include it.

Each record does have a `planning_authority`, an `application_ref` (file number, e.g.
"21/383"), and a `date_received`. What's structurally missing is a clean site_address /
Eircode pair we could join against for geolocation.

# Task

Research whether there is an **official, free or low-cost Irish source** that would let us
reliably backfill or cross-reference Eircodes / structured addresses for planning
applications, given only: planning authority (Galway City or County Council), application
reference number, and approximate development description text. Specifically investigate:

1. **An Bord Pleanála (planning appeals board) public case files** — do their published
   decision documents/case pages include structured site addresses or Eircodes for cases
   that started as Galway City/County applications? Is there a public API or bulk dataset?

2. **MyPlan.ie / the national planning applications portal** — does Ireland have a
   national planning register (e planning.ie or similar) that aggregates all local
   authority planning applications with structured Eircode/address fields, searchable by
   application reference or authority?

3. **Eircode Finder / An Post GeoDirectory** — is there a free or affordable API where we
   could submit a raw address string (like our messy free-text ones) and get a validated
   Eircode back? What are the pricing tiers and rate limits for An Post's GeoDirectory API
   specifically for non-commercial/small-scale research use?

4. **Galway City/County Council's own GIS/open data portals** — do they publish a separate
   structured planning dataset (e.g. via data.gov.ie, Galway County Council's ArcGIS Open
   Data hub, or similar) that includes site coordinates or Eircodes, separate from the
   weekly PDF lists / basic ArcGIS feed we're currently using?

5. **OSi (Ordnance Survey Ireland) or geocoding APIs** — could we geocode the free-text
   townland/street names we do have (even without Eircode) into approximate coordinates
   using a free/open Irish geocoding service, as a fallback if Eircode itself isn't
   obtainable?

# Deliverable

For each source investigated, report:
- Does it exist and is it currently active/maintained?
- Is it free, and if not, what's the pricing model?
- Does it require an API key / registration, and how would we get one?
- Would it actually solve our matching problem (i.e. can we join on application_ref or
  do we still only have address-string fuzzy matching)?
- Any rate limits or usage restrictions relevant to a small research project (not
  processing an entire country's dataset, just Galway, ~21,000 records).

Prioritize official/government sources over paid third-party APIs. Flag anything that
looks like it requires a commercial license before we'd rely on it.
