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
| 3 Full County 2023+ run (Task 6) + 40-item audit (Task 7) | NOT STARTED, see below |
| 4 Chat / left-pane (Tasks 8-10) | PARKED by the owner. No front-end or chat changes. |

Tests: 248 pass (`.venv/bin/python -m pytest -q`). `test_decision_notice_replay.py` skips itself unless the original 172 spike PDFs exist on the machine; that is expected.

## Phase 2 live-run result (100 County apps, seed 42, local DB)
265 documents: 176 validated, 81 no_schedule (third-party cover letters, each in an app that also has a validated notice), 5 needs_ocr, 3 count_mismatch. 96 of 100 applications have at least one validated document. 4 stored validated documents were re-fetched independently: hashes equal, raw_text identical, every item found verbatim in the PDF.

Known, flagged correctly, not blocking: ref 23369 doc 2490638 parsed 6 of 11 (its Final Grant is validated); ref 2460480 parsed 15 vs stated 14.

## Next task: Phase 3 (needs the owner's explicit go-ahead before starting)
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
