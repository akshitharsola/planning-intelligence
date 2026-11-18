# Decision reasons Phase 3: how to test

For reviewing `feat/decision-reasons-phase3`. The steps assume the usual Mac setup (Docker + Python 3.11). Steps 1–3 need no network. Step 6 makes a few polite requests to the council site.

## 1. Set up
```bash
git fetch origin && git checkout feat/decision-reasons-phase3
python3.11 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
cp -n .env.example .env
docker compose up -d
alembic upgrade head                   # must end at 0006
brew install poppler                   # pdftotext; must be poppler, not Xpdf
```
If `pip` installs SQLAlchemy 2.1, run `pip install "sqlalchemy==2.0.51"`. 2.1 makes `postgresql://` look for psycopg 3.

## 2. Run the tests
```bash
pytest -q
```
Expected result:
- Everything passes except `tests/integration/test_chat_service.py::test_answer_question_distinguishes_narrowed_filters_from_out_of_coverage`. It also fails on the base commit, and chat is parked.
- Ingest tests that need the original spike PDFs run only on the machine that has them; elsewhere they skip.

New tests in this branch:
| File | What it checks |
|---|---|
| `tests/integration/test_ingest_decision_documents.py` | Second run downloads no PDFs; `--refresh` re-downloads; `--until-year`; progress every 25 applications; Ctrl-C and resume; unreachable list page counts as a failure; stop after repeated failures |
| `tests/integration/test_decision_data_exchange.py` | Export has no ids; round-trip; re-import changes nothing; relink to local applications; missing application gives a null link; changed hash or parser version replaces items |
| `tests/integration/test_decision_reparse.py` | Dry run writes nothing; re-parse replaces items and records the parser version; second run changes nothing |
| `tests/unit/parsers/test_decision_notice_extractor.py` | Parser v2: "Signed and dated…" text, colon-less "REASON In…" labels, stray "N." lines, real signature lines (all with made-up text) |

## 3. Load the shared data and check it
You need the export file shared privately: `decision_data_20261117T205523Z.jsonl.gz` (parser v2, 16.7 MB, SHA-256 `6b4fffa1…cefa4b4`). Do **not** use the older `…194748Z` file.

```bash
python scripts/ingest_dhlgh.py                       # applications first, so documents can link
python scripts/import_decision_data.py /path/to/decision_data_20261117T205523Z.jsonl.gz
```
- **On a database with no decision documents yet**, the import prints `inserted=9206 updated=0 unchanged=0 items_written=58212 unlinked=0`.
- **If your database still has the Phase 2 trial documents,** some show as `updated` instead; that is fine.
- **Run the import again:** every document should be `unchanged`.

Check the counts in `psql`:
```sql
SELECT extract(year FROM a.decision_date)::int AS year, d.status, count(*)
  FROM decision_documents d JOIN dhlgh_applications a ON a.id = d.dhlgh_application_id
 WHERE d.planning_authority = 'Galway County Council' AND a.decision_date >= '2025-01-01'
 GROUP BY 1, 2 ORDER BY 1 DESC, 2;
```
| Year | validated | no_schedule | count_mismatch | needs_ocr |
|---|---|---|---|---|
| 2026 | 2,609 | 1,596 | 56 | 0 |
| 2025 | 3,090 | 1,773 | 79 | 3 |

On a database holding only this import, these fingerprints should also match:
```sql
SELECT md5(string_agg(concat_ws('|', planning_authority, application_ref, council_doc_id, doc_type, source_url,
       content_sha256, page_count, extraction_method, md5(raw_text), parser_version, status, stated_count,
       target_count, parsed_count, failure_reason, fetched_at, extracted_at), E'\n'
       ORDER BY planning_authority, council_doc_id)) FROM decision_documents;    -- b88f50c08cde54075364af2f092b434a
SELECT md5(string_agg(concat_ws('|', d.planning_authority, d.council_doc_id, i.item_no, i.kind, i.text,
       coalesce(i.reason_text, '<null>')), E'\n' ORDER BY d.planning_authority, d.council_doc_id, i.item_no))
  FROM decision_items i JOIN decision_documents d ON d.id = i.document_id;     -- e92079263e0df53e3ca8f6fb336bb0ab
```

## 4. Check the parser v2 fix
```bash
python scripts/reparse_decision_documents.py --dry-run
```
After importing the v2 file this should report `would change=0`: the stored items already come from parser v2.

To see the fix itself, look at a condition that used to be cut off. Ref 268 (Galway County) is one example: its condition 9 now continues past "…kept in place at all times." with "Signed and dated copies…" and its Reason line.

## 5. Export round-trip (optional)
```bash
python scripts/export_decision_data.py               # writes data/exports/… (gitignored)
```
The output file should list 9,206 documents and 58,212 items. `git status` must stay clean: `data/exports/` and `*.jsonl.gz` are ignored.

## 6. Small live run (optional, uses the network)
This checks the crawler against the council site at 1 request/second with the project User-Agent:
```bash
python scripts/ingest_decision_documents.py --authority "Galway County Council" --since-year 2026 --until-year 2026 --limit 5
```
With the import loaded, all 5 applications show `known=N`: no PDFs are downloaded, only the 5 list pages.

```bash
python scripts/ingest_decision_documents.py --authority "Galway County Council" --refs 2660494 --refresh
```
This downloads that application's PDFs again and should report `skipped` (unchanged), not `stored`.

## What to decide while reviewing
- **Audit:** accept it (0 wrong; 36 exact; 4 differ only by a stripped page header), or not.
- **2024 and 2023:** the runs were skipped; run them later or not.
- **Count mismatches** (135 documents, about 1.5%): keep them hidden; decide whether a parser pass is wanted.
