# Structured Location Data: What We Actually Have, and How to Pitch It

*Planning Intelligence — Internal Briefing*

## 1. The Finding, in Plain Terms

Galway City Council and Galway County Council publish planning-application data with no structured address or postal-code field — just free-text descriptions written by planning officers. We built extraction logic that recovers real, valid postal identifiers hidden incidentally inside that text, where they exist. This turns unusable blob text into structured, queryable location data — a capability that does not exist anywhere else in Irish planning data today, not even in the national DHLGH dataset.

## 2. Current Coverage (Live Data, Verified)

| Council | Total | Has structured code | Address only / neither |
|---|---|---|---|
| Galway City | 1,754 | 940 (53.6%) | 814 (46.4%) |
| Galway County | 20,805 | 9 (0.04%) | 20,796 (99.96%) |
| **Overall** | **22,559** | **949 (4.2%)** | **21,610 (95.8%)** |

The near-total absence of structured codes in County is expected and structural, not a bug or a gap in our extraction — County's official source only ever records a townland name, never a postal code. There was nothing to extract for those 20,796 rows.

Of the 21,610 records without a structured code, 21,603 still have a usable street or townland address, and can be searched by place name today. Only 7 records (all Galway City) have neither an address nor a structured code.

## 3. Your Question: If We Have the Address, Why Can't We Convert It?

This is the single most important thing to get right before the pitch changes. Eircode is not derived from the address itself — it is an arbitrary code assigned to each individual building by An Post when the system launched in 2015, and it lives in exactly one place: An Post / Ordnance Survey Ireland's GeoDirectory database. There is no formula, no open dataset, and no free computation that maps a street address to its Eircode.

> **The phone-number analogy**
>
> Knowing someone's home address doesn't let you compute their phone number — you can only look it up in the phone company's directory. Eircode works the same way. GeoDirectory is that directory, and it is commercially licensed, not public.

In short: address → Eircode is a lookup against a proprietary, paid database — not a coding or engineering problem we can solve for free. This is a licensing question, not a capability gap in our platform.

## 4. What We Checked, and What It Costs

- **An Post GeoDirectory API** — the only authoritative source for real Eircodes. Not a self-serve API: it is a commercial license negotiated directly with An Post's sales team. No public per-record pricing, no free or trial tier found for research use. Wants clean, structured address input, not raw scraped text.
- **Free reverse/forward geocoding (OpenStreetMap / Nominatim)** — real and free, and we've already proven the pattern works at this scale in an earlier exercise. It can produce a clean, human-readable address or area name. It cannot produce an authoritative Eircode — any postcode-shaped value it returns is a crowd-sourced guess, sometimes wrong or missing for rural Irish addresses, and must never be presented as a verified Eircode.
- **Manual lookup via the Eircode Finder website** — the tool originally flagged. It has no public API and no bulk mode; at roughly 15 seconds per address, converting the 21,603 outstanding addresses by hand would take on the order of 90 hours. Not viable as a real pipeline, though usable for a small, hand-picked demo subset if ever needed.
- **Other Irish open data (logainm.ie, data.gov.ie)** — logainm.ie has official townland/placename data, useful for cleaning up area names, but nothing postal-code related. No open Eircode dataset exists in Irish government open data.

## 5. Recommendation

Do not pursue GeoDirectory licensing pre-funding — the cost is disproportionate to a pitch-stage project and would require a negotiated sales conversation, not a quick integration. Instead, position full postal-code coverage as a funded milestone: a concrete, costed capability investors can picture funding, rather than a workaround we half-build for free.

## 6. Vocabulary to Use From Now On

"Eircode" is An Post's registered product name and should not be used loosely once coverage is partial — it risks over-claiming. Use the terms below instead, which are 100% accurate at any coverage level:

| Instead of | Say |
|---|---|
| "Eircode extraction" | "Structured location data extraction" / "postal identifier recovery" |
| "We have Eircodes" | "We recover structured address data other systems discard" |
| "Missing Eircodes" | "The remaining records only have unstructured address text — a paid enrichment step" |

## 7. The Pitch-Ready Paragraph

> "Galway City Council and Galway County Council publish planning-application data with no structured address or postal-code field — just free-text descriptions written by planning officers. We built extraction logic that recovers real, valid postal identifiers hidden inside that text, where they exist, turning unusable blob text into structured, queryable location data — a capability that doesn't exist anywhere else in Irish planning data today, not even in the national DHLGH dataset. Full postal-code coverage across all 22,559+ records, via commercial address-verification licensing, is a funded Phase 2 milestone."

---

*Prepared from live production data, planning-intelligence platform. All figures verified against the running database at time of writing.*
