# Planning Intelligence

Multi-council Irish planning-data ingestion platform. Starts from Galway
City (ported from the `duffy` proof-of-concept) and Galway County (built
fresh), generalizing to support additional councils via the
`/onboard-council` skill.

## Setup

Either Conda or `venv` works — `pyproject.toml` is the single source of
dependency truth either way.

**Conda:**
```bash
conda create -n planning-intelligence python=3.11
conda activate planning-intelligence
pip install -e ".[dev]"
```

**venv:**
```bash
python3.11 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Then:
```bash
cp .env.example .env
docker compose up -d
alembic upgrade head
git config core.hooksPath .githooks
```

The last line is required once per clone — it enables the pre-commit hook
that auto-updates `graphify-out/` (see "Knowledge graph" below). It's a
local git config setting, not something committed to the repo, so every
collaborator runs it themselves right after cloning.

**Windows:** `chmod +x .githooks/pre-commit` is unnecessary (NTFS has no
POSIX exec bit) — just run `git config core.hooksPath .githooks`. Git for
Windows ships Git Bash, which runs the hook's `#!/usr/bin/env bash` script
as-is.

## Running tests

```bash
pytest
```

## Web dashboard

A minimal local dashboard for browsing ingested planning applications.

1. Ensure Postgres is running and `.env` has a valid `DATABASE_URL`
   (see `.env.example`).
2. Install dependencies if you haven't already: `pip install -e .`
3. Start the dashboard:

   ```bash
   uvicorn src.web.main:app --reload
   ```

4. Open `http://localhost:8000` in a browser.

The dashboard shows KPI totals, three charts (monthly applications
received, status breakdown, application type breakdown), and a
filterable/paginated applications table. Click any application reference
to view its full detail page, including provenance fields (source system,
source file, ingestion timestamp, and official source URLs where present).

## Adding a new council

Use the `/onboard-council <county_slug> <region_slug>` skill (see
`.claude/skills/onboard-council/SKILL.md`).

## Knowledge graph

This repo has a navigable knowledge graph at `graphify-out/` (HTML view,
JSON, and `GRAPH_REPORT.md`), committed so it's available immediately after
clone — no setup required. Open `graphify-out/index.html` in a browser, or
read `graphify-out/GRAPH_REPORT.md` for a plain-language summary of the
codebase's structure. See `CLAUDE.md` for the convention collaborators
follow to keep it current after code changes.

It stays current automatically: `.githooks/pre-commit` runs
`graphify update .` and stages the result before every commit, on whoever's
machine is committing. This only works after running
`git config core.hooksPath .githooks` once (see Setup above) — without it,
git silently skips the hook and `graphify-out/` won't update automatically
on that clone.

## Team workflow

This is a two-person project sharing one GitHub repo, both using Claude
Code. To stay in sync and avoid silently diverging:

1. **Pull before starting work.** `git pull origin main` at the start of
   every session, before making changes — picks up the other person's
   merged work and their latest `graphify-out/` snapshot.
2. **Work on a feature branch**, not directly on `main`:
   ```bash
   git checkout -b <yourname>/<short-description>
   ```
3. **Push your branch and open a PR** rather than pushing straight to
   `main`:
   ```bash
   git push -u origin <yourname>/<short-description>
   gh pr create --fill
   ```
   This gives both of you visibility into what the other is building
   before it lands on `main`, and the PR diff naturally includes the
   `graphify-out/` changes from the pre-commit hook, so the graph update
   is reviewable alongside the code that produced it.
4. **Merge via `gh pr merge` or the GitHub UI**, then both pull `main`
   again before starting the next piece of work.

## Collaborators (manual, owner-only)

Team: [tej-juwekar](https://github.com/tej-juwekar).

```bash
gh repo add-collaborator planning-intelligence tej-juwekar --permission push
```

Or via the web UI: `https://github.com/<your-username>/planning-intelligence/settings/access`
→ "Add people" → `tej-juwekar`.

This step is run once, manually, by the repo owner after Task 12 creates
and pushes the repo — see Task 12, Step 8.

### Branch protection (optional, once collaborators are added)

```bash
gh api repos/<your-username>/planning-intelligence/branches/main/protection \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  -f required_pull_request_reviews[required_approving_review_count]=1 \
  -F required_status_checks=null \
  -F enforce_admins=false \
  -F restrictions=null
```
