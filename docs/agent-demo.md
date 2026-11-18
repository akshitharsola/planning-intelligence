# Galway Planning Assistant: demo guide

A standalone prototype (`src/agent/`) that answers questions about Galway planning applications.
It does not use or change the main web app or its chat.

## How it answers
- **Application facts** (status, dates, type, address, appeal) come from the national DHLGH planning register: 22,816 Galway County and City applications.
- **Reasons for refusal and grant conditions** are quoted word for word from Galway County Council decision notices (decisions from 2025 and 2026). Only notices whose item count matches the count the council states are used. Every answer names the document and links to the council's PDF.
- **Topic search** ("refusals about wastewater") uses Postgres full-text search over those checked reasons and conditions.
- When there is no checked text, it says so ("not in our records") and explains why: City, an older year, a scanned notice, or an unconfirmed count.
- An LLM is optional. If Ollama is running, it only helps turn a free-form question into filters; it never writes reasons or conditions. Without Ollama the agent behaves the same, using rules.

## Start it (Windows PC used for the crawl)
1. Start Postgres if the PC was restarted:
   ```bash
   /e/AI_agentic/pg16/pgsql/bin/pg_ctl.exe -D /e/AI_agentic/pg16/data -l /e/AI_agentic/pg16/server.log -o "-p 5432 -c listen_addresses=localhost" start
   ```
2. Start the demo:
   ```bash
   .venv/Scripts/python scripts/run_agent_demo.py
   ```
3. Open http://localhost:8020

On another machine: load the data first (`scripts/ingest_dhlgh.py`, then `scripts/import_decision_data.py <export>`), then step 2.

## Suggested demo flow
| Ask | What it shows |
|---|---|
| Why was application 2660494 refused? | Facts card, both refusal reasons quoted in full, link to the council PDF |
| What conditions apply to 2661255? | 16 grant conditions, each with its "Reason" line |
| Refusals about wastewater in 2026 | Search across all checked refusal reasons, matches highlighted |
| Conditions about flooding in Oughterard | Topic + place filter |
| How many applications were refused in 2025? | Counts across the register |
| Refused applications in Clifden in 2026 | List; click a reference to open it |
| Why was 2361078 refused? | Honest limit: decided in 2024, so "not in our records" with the reason |
| application 2021 | Same reference in County and City: it asks which one |

## Limits to state plainly
- Reasons and conditions: Galway County only, decisions in 2025 and 2026 (about 98% of those decisions). Not City, not earlier years, not scanned notices.
- Applicant names are not in the data.
- The council has not yet been asked about reusing its notice text; confirm before offering this to customers.

## How to test (reviewers)
1. **Data:** follow steps 1–3 of `docs/superpowers/handoff/2026-11-18-phase3-testing-guide.md`: setup, `scripts/ingest_dhlgh.py`, then import the v2 export file.
2. **Tests:** these need the database but no real notice text; they seed made-up applications.
   ```bash
   pytest -q tests/unit/agent tests/integration/test_agent.py
   ```
   They cover:
   - question parsing (references, years, months, places, topics, "may" as a verb);
   - the optional Ollama step (filters validated; rules win);
   - verbatim reasons with their source;
   - only the latest validated document is used;
   - unvalidated text is never shown;
   - a reference in both councils asks which one;
   - topic search;
   - reasons listed by month.
3. **Run it:**
   ```bash
   python scripts/run_agent_demo.py
   ```
   Then open http://localhost:8020.
4. **Expected answers** (with the v2 export loaded and DHLGH data current to 10 Nov 2026):

   | Ask | Expected |
   |---|---|
   | Why was application 2660494 refused? | Refused 3 Nov 2026; 2 reasons quoted; source "Notification of Decision (document 2759004)" with a PDF link |
   | What conditions apply to 2661255? | Granted 10 Nov 2026; 16 conditions, each with its Reason line |
   | Refusals about wastewater in 2026 | 87 applications; best 8 shown with highlighted matches |
   | Conditions about flooding in Oughterard | 7 applications |
   | How many applications were refused in 2025? | 227, across County and City |
   | Reasons for applications refused in March in Galway County | March 2026 (says so); 22 refused, reasons for 21; collapsed rows that expand |
   | Why was 2361078 refused? | "Not in our records" because it was decided in 2024 |
   | application 2021 | Asks: County or City? |
   | City application 22179 | Facts shown; reasons not available for City |

   Counts can drift slightly if your DHLGH load is newer than 10 Nov 2026.
5. **Optional Ollama:** start Ollama with `llama3.1:8b` pulled, then restart the demo. The page footer shows "Question understanding: Ollama + rules". Set `AGENT_USE_OLLAMA=0` to turn it off.

**Not covered here:** the main web app and the parked chat are unchanged. This prototype runs on its own port.
