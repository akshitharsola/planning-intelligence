# Test and push the DHLGH enrichment backfill work

Local `main` is 9 commits ahead of `origin/main`, working tree clean. Run
these from the repo root: `/Users/akshitharsola/Documents/AiAgentic/planning-intelligence`.

## 1. Run the full test suite

```bash
uv run pytest -v
```

Expected: `177 passed`.

## 2. (Optional) Re-verify the enrichment script against the live DB

Only needed if you want to double check the live data again — the backfill
has already been applied and verified. Skip this if you just want to push.

```bash
uv run python scripts/enrich_from_dhlgh.py
```

Expected dry-run output: `Enrichment plan: 0 planned updates.` (all rung-1/2
NULL fields were already backfilled; a nonzero count would mean new data
arrived since the last run).

## 3. Manually test the "Ask Planning Intelligence" chat feature

This is the natural-language chat page — you type a question, Ollama
(`qwen2.5:3b`) extracts the intent, and the app returns matching
applications. Requires Ollama running.

```bash
# Check Ollama is reachable (expect 200)
curl -s http://localhost:11434/api/tags -o /dev/null -w "ollama status: %{http_code}\n"

# Start the app (leave running in this terminal, or add `&` to background it)
uv run uvicorn src.web.main:app --port 8010
```

Then either:

- **In a browser:** open `http://localhost:8010/chat` and type questions like:
  - `What is the status of application 23/119?`
  - `What's new in Oranmore?`
  - `Show granted applications in Tuam`

- **From the terminal**, without a browser:

```bash
curl -s http://localhost:8010/chat -d "question=What is the status of application 23/119?" \
  | grep -A 5 "Interpreted as"
```

Expected: a `Interpreted as: {...}` line showing Ollama's parsed intent,
followed by a results table with the matching application(s). This is the
same flow used to confirm the DHLGH-enriched data (`site_address`) surfaces
correctly end-to-end.

Stop the app afterward with `Ctrl+C` (or `kill` if backgrounded).

## 4. Review what's about to be pushed

```bash
git log --oneline origin/main..main
git status -sb
```

Expected: 9 commits ahead of `origin/main`, working tree clean (`nothing to
commit`).

## 5. Push to GitHub

```bash
git push origin main
```

This pushes directly to `main` on `origin` (`https://github.com/akshitharsola/planning-intelligence`),
matching this project's existing convention of committing directly to main
without feature branches or PRs.
