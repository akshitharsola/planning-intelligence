# Decision Reasons & Conditions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Store the refusal reasons and grant conditions of Galway County decisions (2023–2026, digital-text notices) as citable rows, and let the chat answer "why was this refused / what are the conditions" verbatim from those rows only.

**Architecture:** A pure-text extractor (`src/parsers/decision_notice/`) turns notice text into numbered items and validates the item count against the count the council states. A resumable CLI downloads County notices politely and stores `decision_documents` + `decision_items`. The chat looks reasons up by (planning_authority, application_ref) and renders them word for word with a citation; no row or an unvalidated row means "not in our records" plus a council link.

**Tech Stack:** Python 3, SQLAlchemy 2 + Alembic (Postgres), pdftotext (poppler) via subprocess, urllib/httpx as already used by `src/sources`, FastAPI/Jinja chat, pytest.

**Spec:** `docs/superpowers/specs/2026-11-04-decision-reasons-design.md`

**Spike reference (throwaway, not in repo):** `/private/tmp/claude-501/-Users-akshitharsola-Documents-AiAgentic/6df0c992-c82b-4cdc-b4d0-d1ca911e909c/scratchpad/poc/` — `parse_v2.py` (parser), `pdfs_county/` (172 County PDFs), `results_county.csv` + `results_county2.csv` (per-application metadata incl. `eplan_conditions`). Port its logic; do not import from it.

## Global Constraints

- Natural key everywhere: `(planning_authority, application_ref)`. City and County never mixed; reference numbers collide. Authority values are exactly `Galway County Council` and `Galway City Council`.
- Phase 1 scope is **Galway County Council, decision date 2023-01-01 onward, decision in (`CONDITIONAL`, `REFUSED`)**. City and OCR are out of scope here.
- Status values exactly: `validated`, `count_mismatch`, `needs_ocr`, `no_schedule`, `unparsed`, `unverified`, `batch_order`, `rfi_order`.
- Never silently accept: an item list is `validated` only if parsed count == stated count (County, printed on page 1) or == ePlanning "Number of Conditions" when no stated count exists.
- Crawl: max 1 request/second, honest User-Agent (`planning-intelligence (contact harsolaakshit@gmail.com)`), no logins, no CAPTCHA bypass. A run over more than 150 applications needs the user's explicit go-ahead.
- Do not store PDF files. Store `raw_text`, `source_url`, `content_sha256`.
- Chat answers about reasons come only from `decision_items` rows with `status = validated`. No LLM-generated paraphrase of reason text; the LLM may only be used for intent/filter extraction as today.
- Follow existing conventions: models like `src/core/models/dhlgh_application.py`, migrations like `0005_add_eircode_column.py` (next revision `0006`, down_revision `0005`), CLI like `scripts/ingest_dhlgh.py`.
- After modifying code files run `graphify update .` (AST-only) and include `graphify-out/` in the same commit. Commit only at a phase gate once the user approves.

## Review Focus

- A notice whose numbered footnote steps (appeal instructions 1–7) follow the schedule: must not be counted as items.
- Reference collision: County `2560100` vs City `2560100`; lookups must never return the other authority's reasons.
- Application with two documents (Notification + Final Grant): chat shows items from one document (latest validated), not duplicates.
- Application whose only document is `count_mismatch` or `needs_ocr`: chat says reasons are not in records, shows no extracted text.
- Question about an application with no document at all (e.g. pre-2023, granted-without-conditions): honest "not in our records" plus council link, not an invented reason.
- Re-running the ingest on unchanged documents: no duplicate rows, no re-download of unchanged content.
- Question asking the chat to speculate ("what do you think the council really meant?"): refuses to go beyond the stored text.

## Parked by the user (2026-11-04)

No front-end work (left-pane stats panel, chat page/template changes) until the data foundation is proven. Phases 0–3 are backend and data only. Phase 4 (Tasks 8–10) is on hold until the user lifts this; Task 9's `chat.html` change in particular is front-end.

## Phases and who does what

| Phase | Work | Owner | Gate (return to Claude for verification) |
|---|---|---|---|
| 0 | Port parser into repo with tests | Subagent | Replay on 172 spike PDFs reproduces 155 validated / 3 mismatch |
| 1 | Tables + migration + models | Subagent | Migration up/down, constraint tests |
| 2 | Fetcher + ingest CLI, dry run on 100 apps | Subagent | Claude re-checks counts against live pages |
| 3 | Full County 2023+ run (needs user go-ahead) + independent audit | Subagent runs; **Antigravity audits** | Coverage report + audit of 40 random items vs PDF |
| 4 | Chat integration + guardrails | Subagent; **Antigravity red-teams** | Adversarial question set passes |
| Parallel | OCR bundles/scans, City parser, 2022 County | **Antigravity** (separate prompts) | Each result re-run by Claude before use |

---

## Phase 0 — Extractor

### Task 1: Notice extractor (pure text → items)

**Files:**
- Create: `src/parsers/decision_notice/__init__.py`, `src/parsers/decision_notice/extractor.py`
- Create: `tests/fixtures/decision_notices/` (text files copied from spike PDFs via `pdftotext -layout`, see Step 1)
- Test: `tests/unit/parsers/test_decision_notice_extractor.py`

**Interfaces:**
- Produces:
  - `@dataclass ParsedItem: n: int; text: str; reason_text: str | None`
  - `@dataclass ParsedNotice: status: str; kind: str | None; items: list[ParsedItem]; stated_count: int | None; target_count: int | None; failure_reason: str | None`
  - `def parse_notice(text: str, authority: str, eplan_count: int | None = None, decision: str | None = None) -> ParsedNotice` — `kind` is `"condition"` for grants, `"refusal_reason"` for refusals.
  - `def has_text_layer(text: str) -> bool` — False when fewer than 5 non-blank lines.

- [ ] **Step 1: Create fixtures.** From the spike PDFs run `pdftotext -layout` into `tests/fixtures/decision_notices/<name>.txt` for: `2360654_2469775` (4 refusal reasons), `2260277_2378606` (grant, 17 conditions, C2), `2561413_2669234` (grant, 9, C3 layout), `2261158_2429146` (single unnumbered reason, stated 1), `24155_2549490` (Extension of Duration refusal, inline reason), `2561329_2665281` (stated 14, only 13 present), `2660157_2699960` (3 items, stated 2), `2360744_2474243` (letter, no schedule). Add `<name>.expected.json` with the verified item counts.
- [ ] **Step 2: Write failing tests.** One test per fixture asserting exact `status`, `len(items)`, `stated_count`: 2360654 → validated, 4, stated 4; 2260277 → validated, 17; 2561413 → validated, 9; 2261158 → validated, 1; 24155 → validated, 1; 2561329 → `count_mismatch`, parsed 13, stated 14; 2660157 → `count_mismatch`, parsed 3, stated 2; 2360744 → `no_schedule`. Plus `test_footnote_steps_not_counted` (2360654 items' last text does not contain "You have four weeks"), `test_reason_line_split_for_grants` (2260277 item 1 has non-empty `reason_text`), and `test_blank_text_is_not_text_layer`.
- [ ] **Step 3: Run tests, confirm they fail** — `pytest tests/unit/parsers/test_decision_notice_extractor.py -v` → import errors/FAIL.
- [ ] **Step 4: Implement** `parse_notice` / `has_text_layer` by porting the rules from spike `parse_v2.py`: stated-count regex `\((?:CONDITION NO\.?.?S|REASON\(S\))\s*(\d+)\s*\)` and `conditions?\s+(\d+)\s+set out`; schedule begins at case-insensitive "schedule referred to"; cut at "Footnote:" and signature block; strictly sequential numbering 1,2,3…; accepted delimiters `.` `)`; top-level items only (indent ≤ 6, reject nested sub-numbers and decimals like `1.80`); split grant text at `REASONS?\s*:`; Extension-of-Duration refusals take the inline reason after "For the reason(s) set out hereunder;" as one item; unnumbered single reason when stated count is 1. Strip City watermark tokens only when `authority` is City (port `WM_TOKENS` handling). Status rules per Global Constraints.
- [ ] **Step 5: Run tests, confirm pass.**
- [ ] **Step 6 (gate check): Replay test.** Add `tests/unit/parsers/test_decision_notice_replay.py`, marked `@pytest.mark.skipif` when the spike folder is absent, that runs `pdftotext -layout` + `parse_notice` over all `pdfs_county/*.pdf` with metadata from both results CSVs and asserts: validated == 155, count_mismatch == 3, needs_ocr+no_schedule == 14. This is the proof the port equals the spike.

**Gate 0:** Claude re-runs the replay test and reads 10 random parsed items against PDF text before Phase 1 starts.

---

## Phase 1 — Storage

### Task 2: Models and migration 0006

**Files:**
- Create: `src/core/models/decision_document.py`, `src/core/models/decision_item.py`
- Create: `src/core/db/migrations/versions/0006_create_decision_documents_and_items.py`
- Modify: `src/core/db/migrations/env.py` (import both models, as done for `dhlgh_application`), `src/core/models/__init__.py` if it re-exports models
- Test: `tests/integration/test_decision_tables.py`

**Interfaces:**
- Produces: `DecisionDocument`, `DecisionItem` SQLAlchemy models with exactly the columns in the spec's table section; `DecisionItem.search_vector` is a generated `tsvector` on `text` with a GIN index (follow migration `0003_add_search_indexes.py`); `UniqueConstraint("planning_authority","council_doc_id")` on documents and `UniqueConstraint("document_id","item_no")` on items; index on `(planning_authority, application_ref)`; `document_id` FK `ondelete="CASCADE"`.

- [ ] **Step 1: Write failing integration tests** in `test_decision_tables.py` (pattern of `tests/integration/test_dhlgh_pipeline_end_to_end.py`, real `SessionLocal`, clean up): `test_insert_document_with_items_roundtrip`; `test_duplicate_council_doc_id_per_authority_rejected` (IntegrityError); `test_same_council_doc_id_other_authority_allowed`; `test_duplicate_item_no_rejected`; `test_delete_document_cascades_items`; `test_search_vector_matches_word` (item text "boundary wall" matches `to_tsquery('wall')`).
- [ ] **Step 2: Run and confirm FAIL** (tables missing).
- [ ] **Step 3: Write models and migration 0006** (`revision="0006"`, `down_revision="0005"`); no explicit duplicate indexes.
- [ ] **Step 4: Apply** `alembic upgrade head`, run the tests, confirm PASS; also run `alembic downgrade -1` then `upgrade head` to prove both directions.
- [ ] **Step 5: Run the full suite** (`pytest`) — all prior tests still pass (baseline was 145+).

**Gate 1:** Claude checks the migration SQL (`alembic upgrade head --sql`) matches the spec table-by-table.

---

## Phase 2 — Fetch and ingest (dry run)

### Task 3: County document fetcher

**Files:**
- Create: `src/sources/galway/decision_documents.py`
- Test: `tests/unit/sources/test_decision_documents.py`
- Fixture: `tests/fixtures/galway_county_doc_list.html` (saved copy of `https://apps.galwaycoco.ie/ViewExternalDocuments/?RefNo=26136`)

**Interfaces:**
- Produces:
  - `@dataclass DocLink: council_doc_id: str; doc_type: str; url: str`
  - `def list_decision_docs(html: str, ref: str) -> list[DocLink]` — only types "Notification of Decision" → `notification_of_decision`, "Final Grant" → `final_grant`; `url` is `https://apps.galwaycoco.ie/ViewExternalDocuments/ViewPDF.aspx?RefNo=<ref>&ViewFind=true&ref=<DocID>`; `council_doc_id` is `<DocID>`.
  - `class CountyDocFetcher: __init__(self, min_interval: float = 1.0, user_agent: str = ...)`; `fetch_list(ref: str) -> str`; `fetch_pdf(link: DocLink) -> bytes | None` (None unless body starts with `%PDF`); a shared rate limiter guarantees ≥ `min_interval` seconds between any two requests.
  - `def fetch_eplanning_condition_count(ref: str) -> int | None` using regex `Number of Conditions:\s*(\d+)` on `https://www.eplanning.ie/GalwayCC/AppFileRefDetails/<ref>/0`.

- [ ] **Step 1: Failing tests:** `test_list_decision_docs_filters_types` against the saved fixture; `test_url_shape`; `test_fetch_pdf_rejects_html` (fake opener returns HTML → None); `test_rate_limiter_spaces_requests` (inject fake clock/sleep, assert ≥1.0 s between three calls); `test_condition_count_regex` on a saved snippet.
- [ ] **Step 2: Confirm FAIL.** **Step 3: Implement** (port spike `county_poc.py`; inject the opener/clock so tests need no network). **Step 4: Confirm PASS.**

### Task 4: Ingest CLI

**Files:**
- Create: `src/pipelines/decision_documents.py`, `scripts/ingest_decision_documents.py`
- Test: `tests/integration/test_ingest_decision_documents.py`

**Interfaces:**
- Consumes: Task 1 `parse_notice`, `has_text_layer`; Task 2 models; Task 3 fetcher (injectable, so tests pass a fake).
- Produces:
  - `def ingest_application(session, fetcher, application: DHLGHApplication) -> IngestResult` where `IngestResult` has `documents_stored: int`, `documents_skipped_unchanged: int`, `statuses: dict[str, int]`.
  - CLI `python -m scripts.ingest_decision_documents --authority "Galway County Council" --from-date 2023-01-01 --limit N [--refs R1,R2] [--dry-run]`. Selection: `dhlgh_applications` rows for that authority with `decision in (CONDITIONAL, REFUSED)` and `decision_date >= from-date`, ordered by `decision_date`, skipping applications whose documents are already stored with the same `content_sha256`. It prints a one-line summary per application and a final status histogram.
  - For each document: `pdftotext -layout` → `has_text_layer`? else status `needs_ocr`; `parse_notice(text, "Galway County Council", eplan_count=fetcher.fetch_eplanning_condition_count(ref), decision=app.decision)` (eplan count fetched only when no stated count); store `raw_text`, hash, `parser_version` (constant `"1"`), items.

- [ ] **Step 1: Failing integration tests with a fake fetcher serving fixture PDFs/text:** `test_validated_notice_stores_document_and_items`; `test_count_mismatch_stored_with_status_and_no_items_shown_as_validated` (items may be stored but document `status=count_mismatch`); `test_scan_stored_as_needs_ocr_without_items`; `test_rerun_unchanged_creates_no_duplicates` (row counts identical, `documents_skipped_unchanged == n`); `test_same_ref_other_authority_not_touched` (seed a City app with the same ref; only County rows change); `test_dry_run_writes_nothing`; `test_fetch_failure_does_not_abort_run` (one ref raises; others stored; failure counted).
- [ ] **Step 2: Confirm FAIL. Step 3: Implement** (idempotent upsert on `(planning_authority, council_doc_id)`; replace items when hash changed). **Step 4: Confirm PASS; run full suite.**

### Task 5: Live dry run on 100 applications

**Files:** none (verification task; output saved to `docs/superpowers/plans/2026-11-04-decision-reasons-phase2-report.md`)

- [ ] **Step 1:** Run `python -m scripts.ingest_decision_documents --authority "Galway County Council" --from-date 2023-01-01 --limit 100` (≈ 100 apps × ~4 requests at 1 req/s; tell the user before starting).
- [ ] **Step 2:** Record the status histogram and the list of every non-`validated` document with reason.
- [ ] **Step 3:** Re-run the same command; assert nothing new is stored.

**Gate 2:** Claude independently verifies: validated rate vs spike (expect ≈ 95%), 10 random stored items against the council PDF text, and that no City rows were created.

---

## Phase 3 — Full County run and independent audit

### Task 6: Full run (requires explicit user go-ahead)

- [ ] **Step 1:** Show the user the size (`SELECT count(*)` of eligible applications) and estimated hours; wait for a yes.
- [ ] **Step 2:** Run the CLI without `--limit` in the background in resumable batches; if interrupted, re-running continues without duplicates.
- [ ] **Step 3:** Write `phase3-coverage-report.md`: counts by year × status, % of eligible applications with ≥1 validated document, list of `count_mismatch` documents.

### Task 7: Independent audit (Antigravity)

- [ ] **Step 1:** Claude exports a random sample of 40 stored items (seeded, mixed years, grants and refusals) to `audit_sample.csv` with application_ref, council_doc_id, item_no, stored text, source_url.
- [ ] **Step 2:** Antigravity prompt (offline except opening the stored source PDFs the user already allows): for each row, compare stored text to the PDF page image/text and mark `exact` / `minor_diff` / `wrong` / `missing_words`, quoting the difference. It must not edit the parser.
- [ ] **Step 3:** Claude re-checks every non-`exact` row itself before accepting the result.

**Gate 3 (decision point for the user):** accept coverage and audit results (target: 0 `wrong`, ≥ 95% `exact`) or return to Phase 0 rules.

---

## Phase 4 — Chat integration and guardrails

### Task 8: Reasons service

**Files:**
- Create: `src/services/decision_reasons_service.py`
- Test: `tests/integration/test_decision_reasons_service.py`

**Interfaces:**
- Produces:
  - `@dataclass ReasonsResult: found: bool; authority: str; application_ref: str; kind: str | None; doc_type: str | None; source_url: str | None; items: list[ItemView]; message: str`
  - `@dataclass ItemView: n: int; text: str; reason_text: str | None`
  - `def get_reasons(db: Session, planning_authority: str, application_ref: str) -> ReasonsResult` — returns items only from the latest `validated` document (highest `council_doc_id` of the newest doc type) for exactly that authority and ref; otherwise `found=False` and `message` = "The reasons for this decision are not in our records." plus the council page link from `dhlgh_applications.official_detail_url`.

- [ ] **Step 1: Failing tests:** `test_returns_items_from_validated_document`; `test_authority_isolation` (County ref `X` and City ref `X` each return only their own text); `test_two_documents_returns_one_set_not_both`; `test_count_mismatch_only_returns_not_found`; `test_needs_ocr_only_returns_not_found`; `test_unknown_application_returns_not_found_without_error`.
- [ ] **Step 2–4:** Confirm FAIL, implement, confirm PASS.

### Task 9: Chat wiring

**Files:**
- Modify: `src/services/chat_service.py` (new branch in `answer_question`), `src/web/templates/chat.html` (render an items block with citation)
- Test: `tests/unit/services/test_chat_reasons.py`

**Interfaces:**
- Consumes: `get_reasons` (Task 8). Existing `answer_question(db, question) -> result` shape is preserved; add a `reasons` field to the result.
- Produces: intent detection `def is_reasons_question(question: str) -> bool` (deterministic keyword rules: "why", "reason", "refus", "reject", "condition" with an application reference or an address that resolves to exactly one application); resolution of the target application via the existing filter extraction; if more than one application matches, the answer lists them and asks which, and shows no reasons.
- Rendered answer format: `Refused on <date>. Reasons from the council's notice (<doc_type>, <authority>, ref <ref>):` then each item `<n>. <text>` verbatim, then `Source: <source_url>`. Items from scans (`extraction_method='ocr'`) are not shown in Phase 4 (they have status `needs_ocr` or are out of scope).

- [ ] **Step 1: Failing tests (stub LLM client and DB seed):** `test_why_refused_question_returns_verbatim_items`; `test_answer_contains_citation_and_source_url`; `test_no_validated_rows_says_not_in_records_and_links_council`; `test_ambiguous_application_asks_which_and_shows_no_reasons`; `test_llm_output_never_appears_in_reasons_block` (stub LLM returns "INVENTED REASON"; assert absent from the answer); `test_non_reasons_question_unchanged` (existing count/list questions keep current behavior); `test_speculation_request_refused` ("what do you think the council really meant" → standard not-in-records style reply, no paraphrase).
- [ ] **Step 2–4:** Confirm FAIL, implement, confirm PASS; run the full suite.
- [ ] **Step 5: Manual check in the browser** at `http://localhost:8010/chat` for one validated refusal, one grant with conditions, one application with no document — screenshot or paste output in the gate report.

### Task 10: Red-team (Antigravity)

- [ ] **Step 1:** Antigravity prompt: against the running chat, ask 60 questions (reasons, conditions, wrong refs, City vs County collisions, prompts trying to make the chat use web knowledge or invent a reason, questions about scans/old years) and report every answer that contains text not present in `decision_items` for the cited application.
- [ ] **Step 2:** Claude reproduces each reported failure, fixes with a test first, re-runs the set.

**Gate 4:** user approval to enable for internal use. Showing it to customers remains blocked until the open question on council reuse permission is answered.

---

## Parallel tracks (Antigravity, separate prompts; none block Phases 0–4)

1. **OCR bundles:** split decision notices from screenshot/appeal pages in scanned PDFs, accept `N:` numbering, re-test on the 2 failed fresh scans plus 20 new scans.
2. **City parser on fresh City sample** (digital text; 44/44 earlier, needs an unseen sample).
3. **2022 County** after OCR improves.

Each returns a results table; Claude re-runs it before anything enters the repo.

## Self-review notes

- Spec coverage: tables (Tasks 2), statuses and counts (1, 4), answering rules incl. verbatim + citation (8, 9), extraction job rules (3, 4, 6), calls/non-goals respected (no PDFs stored, no City, no OCR). The spec's open questions (reuse permission, show mismatches, coverage figure) are not decided here: mismatches stay hidden, no coverage figure is built, and permission gates customer exposure at Gate 4.
- Out of scope, not forgotten: left-pane stats panel from the original request (separate plan after this one).
- Types and names checked across tasks: `parse_notice`, `ParsedNotice`, `ParsedItem`, `DocLink`, `CountyDocFetcher`, `ingest_application`, `get_reasons`, `ReasonsResult`, `ItemView`.
