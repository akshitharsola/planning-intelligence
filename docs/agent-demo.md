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
