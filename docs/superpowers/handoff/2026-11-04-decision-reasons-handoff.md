# Decision reasons: handoff (2026-11-04)

Read first: spec `docs/superpowers/specs/2026-11-04-decision-reasons-design.md`, plan `docs/superpowers/plans/2026-11-04-decision-reasons.md`.

## What this is
Store refusal reasons and grant conditions from Galway County Council decision-notice PDFs (2023+, digital text) as citable DB rows. An item is shown as fact only if the parsed item count equals the count the council states (or ePlanning's "Number of Conditions"). The future chat answers only from these rows, never from web knowledge.

## Status
| Phase | State |
|---|---|
| 0 Extractor (`src/parsers/decision_notice/`) | done, verified |
| 1 Schema (models, migration 0006) | done, verified |
| 2 Fetcher, pipeline, CLI (Tasks 3-4) + live run on 100 apps (Task 5) | done, verified |
| 3a Resumable runs + data hand-back (`--skip-known`/`--refresh`, `--until-year`, progress log, stall stop, export/import scripts) | done, verified (branch `feat/decision-reasons-phase3`) |
| 3b County run 2026 + 2025 (Task 6) | done, verified from SQL (2026-11-17), see "Phase 3 results" |
| 3c County run 2024 + 2023 | SKIPPED by the owner (2026-11-17); not run |
| 3d 40-item audit (Task 7) | done: 0 wrong, 36 exact, 4 not-exact (page header removal only), see below |
| 3e Parser v2 fix + offline re-parse | done, verified (102 items corrected, see "Parser v2 fix") |
| 4 Chat / left-pane (Tasks 8-10) | PARKED by the owner. No front-end or chat changes. |

Tests (Windows, 2026-11-17): 260 pass, 6 skip, 1 fail. Skips: `test_decision_notice_replay.py` and 5 ingest tests that need the original spike PDFs (not committed). The failure, `test_chat_service::test_answer_question_distinguishes_narrowed_filters_from_out_of_coverage`, also fails on the base commit; chat is parked, so it was not touched.

## Phase 3 results (County, local DB, numbers from SQL)
Data stays in the local DB and in a private export file (`scripts/export_decision_data.py`, written to gitignored `data/exports/`). Load it elsewhere with `scripts/import_decision_data.py <file>` after `scripts/ingest_dhlgh.py`.

Eligible counts on 2026-11-17 (DHLGH data to 2026-11-10): 2023 1534, 2024 1680, 2025 1715, 2026 **1556** (was 958 on 2026-11-04). Total 6485.

| Year | Eligible apps | Docs | validated | no_schedule | count_mismatch | needs_ocr | Items | Apps with a validated doc | Wall time |
|---|---|---|---|---|---|---|---|---|---|
| 2026 | 1556 | 4261 | 2609 | 1596 | 56 | 0 | 25923 | 1534 (98.6%) | 2 h 07 min |
| 2025 | 1715 | 4945 | 3090 | 1773 | 79 | 3 | 32289 | 1680 (98.0%) | 2 h 38 min |

- Fetch failures: 2026 none. 2025: 3 PDF read timeouts, all on ref 2461734; a single `--refs 2461734` retry fetched all 3 (included above).
- First 2026 attempt (2026-11-14) stopped at app 5: apps.galwaycoco.ie refused connections from this network for a period; nothing stored. Fix added: unreachable list pages now count as failures and a run stops after 10 failed apps in a row.
- Apps with no decision notice or final grant on their list page (nothing stored, not a failure): 2026: 2660528, 2661435. 2025: 24254, 2560548.
- Apps with documents but none validated: 20 in 2026, 33 in 2025 (count mismatches, plus 2 scans in 2025). Nearly all no_schedule documents (1572 of 1596, 1741 of 1773) sit in an app that also has a validated notice.
- count_mismatch is mostly under-parsing (2026: 48 under, 8 over; 2025: 62 under, 17 over). Large gaps (e.g. 5 of 31, 2 of 18) suggest numbering the parser does not handle: candidate for a later parser pass.

### Task 7 audit (2026-11-17)
40 items sampled from 57,074 validated items (Python `random.Random(42)`, 21 from 2025, 19 from 2026, 39 conditions, 1 refusal reason). Each source PDF re-fetched at 1 req/s with the project User-Agent; all 40 sha256 equal to the stored hash. Stored text (and reason text) compared word by word with two independent extractions of the fresh PDF (poppler `pdftotext -layout` and pdfplumber); both agreed on every item.
- **wrong: 0.**
- **exact: 36 (90%).**
- **not-exact: 4 (10%)**: refs 2660703 #10, 2461768 #6, 2660259 #6, 2561086 #18. Each item crosses a page break; the only difference is the page number plus the running header "Schedule Referred To - Planning Reference No. …", which the parser strips by design. No word missing or changed.
- Boundaries checked for all 40: each item starts after its own number and ends at its "Reason:" line followed by the next item number, a page number, or (for the 5 final items) the notice footnote.
- Against the plan's target (0 wrong, ≥95% exact): 0 wrong is met; strict word-for-word exact is 90%, below 95%. Counting page-header removal as exact, it is 40/40. Owner to decide which reading applies.

### Parser v2 fix (2026-11-17, after the audit)
Counting empty `reason_text` fields exposed defects the count check cannot catch (the item count stays right):
- A condition line starting "Signed and dated copies…" was taken as the signature block, cutting the condition and its reason short: 75 items (74 in validated documents, 46 applications).
- "REASON In…" / "Reason; In…" labels without a colon left the reason inside the condition text: 26 items.
- A stray "N." line above the previous item's Reason line shifted text and reason between two items (1 document).

Fix in `src/parsers/decision_notice/extractor.py` (`PARSER_VERSION = "2"`), with tests on synthetic notices. `scripts/reparse_decision_documents.py` re-parses stored `raw_text` (no network; `--dry-run` first). Result: 97 documents / 102 items changed, every change checked (new text verbatim in the notice, no words lost); no status changed; status counts above are unchanged. Conditions with no reason fell from 117 to 16; no "Signed and dated" truncations remain. The import now also replaces items when `parser_version` differs, so a re-parsed export upgrades an earlier import.

Current export: `decision_data_20261117T205523Z.jsonl.gz` (parser v2). The earlier `…194748Z` file is parser v1 and should not be used.

## Windows setup notes (2026-11-17)
No Docker on the run machine: Postgres 16.10 (EDB portable zip) + PostGIS 3.4.2 (OSGeo bundle) outside the repo, same user/db as `docker-compose.yml`. Python 3.13 venv; SQLAlchemy pinned to the `uv.lock` version 2.0.51 because 2.1 defaults `postgresql://` to psycopg 3. Git for Windows ships Xpdf `pdftotext` 4.00, not poppler: put a poppler build (26.11 used here, via conda-forge) first on PATH. graphify was not installed, so `graphify-out/` was not updated.

## Phase 2 live-run result (100 County apps, seed 42, local DB)
265 documents: 176 validated, 81 no_schedule (third-party cover letters, each in an app that also has a validated notice), 5 needs_ocr, 3 count_mismatch. 96 of 100 applications have at least one validated document. 4 stored validated documents were re-fetched independently: hashes equal, raw_text identical, every item found verbatim in the PDF.

Known, flagged correctly, not blocking: ref 23369 doc 2490638 parsed 6 of 11 (its Final Grant is validated); ref 2460480 parsed 15 vs stated 14.

## Original Phase 3 brief (kept for reference; see Status and "Phase 3 results" for what was done)
Eligible: 5,887 County applications (2023: 1534, 2024: 1680, 2025: 1715, 2026: 958), roughly 15,600 documents, about 10 hours at 1 req/s. Writes to the LOCAL docker DB only. Data in one person's local DB is not shared with others.

Steps:
1. Add `--skip-known` (default on for authority runs): skip PDFs whose (authority, council_doc_id) is already stored; list pages are still fetched. `--refresh` re-checks hashes. Tests: second run makes zero PDF requests; `--refresh` re-fetches.
2. Progress logging every 25 applications; safe to Ctrl-C and resume.
3. Add `--until-year` (with a test). Run year by year, smallest first (2026, 2025, 2024, 2023), in the background with a log file.
4. After each year report: status histogram, failures with reasons, every non-validated ref with failure_reason, wall time. Check the numbers against the DB, not against the run's own summary.
5. Task 7: audit 40 random validated items against the source PDFs. Target 0 wrong, at least 95% exact.

## Rules that must not be broken
- Network: 1 request per second, User-Agent `planning-intelligence (contact harsolaakshit@gmail.com)`, no logins, no CAPTCHA bypass. Stop on repeated 429/403.
- Never store PDFs. Store `raw_text`, `source_url`, `content_sha256`.
- `validated` only when parsed count equals stated/ePlanning count. `unverified` items (no count) are never shown as fact.
- (planning_authority, application_ref) is the key; City and County refs collide.
- No front-end, chat or template changes until the owner lifts the park.
- After code changes run `graphify update .` (the pre-commit hook does this).

## Not in scope here (separate tracks)
OCR for scans (`needs_ocr`), Galway City on a fresh sample, 2022 County.

## Open questions for the owner
Council reuse permission before showing extracted text to customers; show or hide count_mismatch items (draft: hide); a coverage figure in the left pane.

## Setup
`docker compose up -d`, `alembic upgrade head` (reaches 0006), `.env` from `.env.example`.
