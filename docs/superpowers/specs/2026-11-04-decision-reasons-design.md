# Decision reasons & conditions: design (DRAFT for approval)

Status: draft, nothing built. Based on the throwaway spike in the session scratchpad.

## Why
The database stores outcome and dates for each application, but not *why* it was refused or *what conditions* a grant carries. That text exists only in the council decision-notice PDFs. The AI chat must answer only from our own stored data (no web, no guessing), so those texts must be stored, with a trail back to the source.

## Goals
- Store each decision's refusal reasons / grant conditions as separate, citable items.
- Every item traces to a council document (authority, ref, document type, item number, source link).
- Every extraction carries an honest status. Count-checked items are distinguished from unchecked ones.
- County first (92% of data). City stays separate; same tables, never mixed: every lookup uses (planning_authority, application_ref).

## Non-goals
- OCR is a second-phase add-on (pipeline proven offline, see below). Phase 1 loads digital-text notices; scans get status `needs_ocr` until the OCR pipeline is productionised.
- No appeals (An Coimisiún Pleanála) in this phase.
- No AI or UI changes in this phase. This spec covers storage and extraction only. The chat/left-pane use is a follow-up spec.
- Not storing the PDF files themselves (see Calls).

## Anti-goals
- A silently wrong or merged condition shown as fact.
- Any answer built from web knowledge when our rows are missing.

## Evidence it works (spike, offline)
- County, fresh unseen sample (104 docs, 2023–2026): 99 validated (95%), 3 count mismatches (flagged), 2 scans.
- County 2024–2026 in the first sample: 39/39 validated. 2022 has many scans.
- "Validated" means parsed item count equals the count the council states in the notice (County) or on its ePlanning page (City). It does not prove each item's wording is complete; a human spot check of 10 documents found no truncation or merging.

## Tables

### `decision_documents` (one row per downloaded notice)
| column | type | notes |
|---|---|---|
| id | uuid pk | |
| planning_authority | text | same values as `dhlgh_applications` |
| application_ref | text | normalised as there |
| dhlgh_application_id | uuid fk → dhlgh_applications.id, nullable | null if no match |
| council_doc_id | text | council's own document id |
| doc_type | text | `notification_of_decision` / `final_grant` / `chief_executives_order` |
| source_url | text | link to the council's viewer page |
| content_sha256 | text | change detection |
| page_count | int | |
| extraction_method | text | `pdftotext` or `ocr` (OCR text can contain recognition errors) |
| raw_text | text | full extracted text, for audit and re-parsing |
| parser_version | text | re-run when parser improves |
| status | text | `validated` / `count_mismatch` / `needs_ocr` / `no_schedule` / `unparsed` / `unverified` / `batch_order` / `rfi_order` (the last two: not decision notices, kept for audit, never shown as reasons) |
| stated_count | int null | count printed in the notice (County) |
| target_count | int null | count used for validation |
| parsed_count | int | |
| failure_reason | text null | |
| fetched_at, extracted_at | timestamp | |
Unique: (planning_authority, council_doc_id). Index: (planning_authority, application_ref).

### `decision_items` (one row per condition or refusal reason)
| column | type | notes |
|---|---|---|
| id | uuid pk | |
| document_id | uuid fk → decision_documents.id on delete cascade | |
| item_no | int | number printed in the notice |
| kind | text | `condition` / `refusal_reason` |
| text | text | the condition or reason text |
| reason_text | text null | the "Reason:" line attached to a grant condition |
| search_vector | tsvector (generated) | GIN index, same style as migration 0003 |
Unique: (document_id, item_no).

One application can have several documents (e.g. Notification and Final Grant). Chat reads the latest `validated` document per application; others stay for audit.

## OCR findings (offline spike, Antigravity, re-run and checked)
- Local tesseract at `--psm 6` plus layout reconstruction and a small text normaliser: 11/11 County scans and 9/9 City scan decision notices pass the count check. About 3.7 s per page at 300 dpi.
- The other 11 City "scans" are not decisions: 8 are one-page batch confirmation orders (checked against the page image: a list of refs, no conditions) and 3 are Article 33(1) requests for further information.
- Count-passing is not word-accurate: spot checks found errors like "tn accordance", "ta the", "Ithas". So OCR-derived items are `validated` for count but must be shown as scanned text, with the original link, never as verbatim quotes.
- Samples are small (11 + 9 documents). Expect lower rates on a larger scan set.

## Rules for answering (used by the follow-up spec)
- Only `validated` items are stated as fact. Every statement cites authority, ref, doc type, item number and the source link.
- Items from `extraction_method = ocr` carry a note that they come from a scan and may contain recognition errors.
- `count_mismatch`, `needs_ocr`, `no_schedule`, `unverified`, or no row: say "the reasons are not in our records", link to the council page, and show nothing extracted.
- No web or general knowledge for decision reasons, ever.

## Extraction job (scope for the plan)
- Separate CLI, resumable, idempotent (skips unchanged `content_sha256`).
- 1 request per second, honest User-Agent, no logins or CAPTCHA bypass. County viewer first.
- Starts with a dry run on ~100 apps, then a full 2023–2026 County run, only after approval (about 5,900 notices, hours at 1 req/s).
- Alembic migration 0006 creates both tables; models follow `dhlgh_application.py` conventions.

## Calls I made (change any)
1. Do not store PDF files. Store extracted text plus source URL and hash. Reason: reuse permission is unknown and the PDFs carry an "inspection purposes only" watermark.
2. Both authorities share the same two tables, separated by `planning_authority`.
3. Grant conditions and refusal reasons share one table with a `kind` column.
4. Failed or unverified documents are stored with status, not dropped, so coverage can be measured.
5. Start with 2023–2026 only; 2022 and earlier wait for OCR.

## Open questions for the owner
- Reuse permission: should we ask Galway County Council in writing before showing extracted text to customers? (Recommended before launch; not needed for local testing.)
- Show `count_mismatch` items marked "needs review", or hide them? (Draft says hide.)
- Should the left pane show a coverage figure ("reasons available for X% of decisions")?
