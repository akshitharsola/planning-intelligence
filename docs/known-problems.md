# Known Problems / Next Session Agenda

Written 2026-07-02, end of session. Purpose: resume cleanly without
re-deriving context. Nothing here has been fixed yet unless marked DONE.

## 0. Session state at time of writing

- Both dev servers (main dashboard + worktree chat) were killed before
  ending this session. Nothing should be running.
- Worktree lives at `.claude/worktrees/web-dashboard`, branch
  `worktree-web-dashboard`, pushed to GitHub up to commit `0b0134d`.
- Main repo `main` pushed up to commit `6dbe99a`.
- Current DB scale: 20,531 applications total (203 Galway City Council,
  20,328 Galway County Council), date range 2016-01-04 to 2026-07-02.
  All from Galway. No other counties ingested yet.

## 1. User's top-level concern: "the AI chat is a very small thing"

The user's framing at end of session: the chat feature is a thin layer
on top of what actually matters, which is the DB and backend underneath
it. Before doing more chat polish, we need to figure out what "better
DB and backend system" means concretely. This needs a real discussion,
not assumptions. Candidate angles to raise next session:

- Is the concern about **scale** (only 1 county pair ingested so far,
  need many more councils)?
- Is it about **schema/data-model maturity** (current schema is one
  flat `applications` table + `application_events` — is that the right
  shape long-term, e.g. for cross-county queries, historical status
  tracking, or richer entities like sites/agents/decisions)?
- Is it about **reliability of the ingestion pipeline** (still one
  scraper + one parser per council, hand-fitted to each PDF/site
  layout — doesn't scale to many councils without a lot more parser
  engineering)?
- Is it about **query/API performance** as data grows (no indexing
  strategy discussed yet, no caching, dashboard queries run live
  against Postgres on every request)?
- Something else the user has in mind but hasn't said yet — ask
  directly rather than guessing.

This is the first thing to resolve next session, before touching chat
UI or chat accuracy further.

## 2. Confirmed bugs in the AI chat feature (found via live testing 2026-07-02)

### 2a. Relative dates resolve to the wrong year (CONFIRMED, not fixed)

Asked: "What's new in Tuam for last month" (today's real date is
2026-07-02). Got back:
```
Interpreted as: {'date_received_from': '2023-06-01', 'date_received_to': '2023-07-01', 'q': 'Tuam'}
```

The LLM resolved "last month" to June **2023**, not June 2026. This is
a pure model date-math failure — `llama3.1:8b` doesn't reliably know
today's date. The extraction prompt in `chat_service.py` never tells
the model what today's date actually is, so it's guessing from training
data patterns.

**Fix direction (not yet implemented):** pass the real current date
into the system prompt explicitly (e.g. "Today's date is 2026-07-02.
Resolve relative date phrases like 'last month' against this date, not
your training data.") — this is a well-known mitigation for this exact
class of LLM failure. Should verify it actually fixes it, not just
assume the prompt change works — Ollama's smaller models can still get
this wrong even when told.

### 2b. Free-text `q` field can't express compound/structured intent (CONFIRMED, not fixed)

Asked: "What's new in Tuam for last month (May)". Got back:
```
Interpreted as: {'q': 'Tuam AND 2023-05'}
```
Result: 0 matches (correctly reported as 0, but for the wrong reason —
the DB has no way to match a literal string `"Tuam AND 2023-05"`
against free text columns via ILIKE).

Two compounding problems here:
1. The model tried to cram a date expression into the `q` field
   instead of using `date_received_from`/`date_received_to`, even
   though the extraction prompt explicitly separates those concepts.
2. `q` is implemented as a single ILIKE-across-three-columns match
   with no boolean operator support — even if the model behaved, `q`
   itself can't express "AND" semantics. This is a structural
   limitation of `application_service.search()`, not just a prompt
   problem.

**Fix direction (not yet implemented):** likely need (a) few-shot
examples in the extraction prompt showing date phrases going into the
date fields, not `q`, and (b) possibly reconsider whether `q` should
support multiple independent keywords ANDed together at the SQL level,
since users will naturally phrase compound queries this way.

### 2c. (Already fixed this session, confirmed working) planning_authority guessed from place names

Was: asking about "Tuam" caused the model to infer
`planning_authority: 'Galway County Council'` even though the prompt
said not to guess unnamed fields. Fixed in commit `0b0134d` by
explicitly telling the model not to infer authority from place names.
Verified fixed via live re-test. Not an open item, listed here only
for continuity/context.

### 2d. Answer failed to disclose "these are examples, not the full list"

Was: for a 708-match query, the LLM's prose only described 3 examples
and stated a total count, but didn't make clear the 3 were a small
sample of 708 rather than a complete answer. Fixed in the same commit
`0b0134d` by having the summarization prompt explicitly say so when
total > rows shown. Verified fixed via live re-test ("These are only a
few examples out of the total matches of 712."). Not an open item,
listed here only for continuity/context.

## 3. UI is explicitly deferred, not forgotten

User confirmed UI polish (styling, layout, `/chat` page look, results
table presentation) can wait — it's real but lower priority than the
DB/backend and chat-accuracy questions above. Currently the whole app
(dashboard + chat) is unstyled/minimal HTML with only
`src/web/static/app.css` for baseline styling. Revisit once the
higher-priority items are resolved.

## 4. Previously flagged, still open from earlier in the project

- Only Galway City + County are ingested. No other Irish planning
  authorities yet — directly related to item 1's scale question.
- No authentication/access control on the dashboard or `/chat` route —
  fine for local-only use, becomes a real question if this is ever
  exposed beyond localhost/LAN.
- `LLM_BACKEND=hosted_api` path (`HostedApiClient`) exists in code but
  has never been tested against a real hosted API — only the Ollama
  path has been verified live.

## 5. Explicitly NOT problems (verified working, don't re-litigate)

- Dropdown/chart scoping to selected planning_authority — fixed and
  tested.
- `is_plausible_application_row` data-quality guard — fixed, tested,
  and already caught a real bug (Firvalidated PDF `file_number`
  corruption) which was itself found and fixed this session.
- Firvalidated PDF `file_number` reading as literal `'F'` — root-caused
  (empty header column collision in `_map_column`) and fixed in commit
  `6dbe99a`, verified via live re-download + dry-run ingest showing
  rejected count dropped from 29 to 0.
- Basic filter-extraction → search() → summarize() pipeline works and
  degrades gracefully when Ollama is unreachable (tested both ways).
- Jetson AGX Orin + Ollama + `llama3.1:8b` is live and reachable at
  `192.168.0.223:11434`, confirmed working end-to-end from the chat UI.
