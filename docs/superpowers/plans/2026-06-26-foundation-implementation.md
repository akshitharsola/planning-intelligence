# Planning-Intelligence Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Execution status note (2026-06-27):** Due to a token/session budget
> constraint, only Task 1 (repo scaffold) was executed and pushed to
> GitHub in the originating session. Tasks 2-12 are **not yet started** —
> they are written in full, ready to be picked up by either collaborator
> ([@harsolaakshit](https://github.com/harsolaakshit) or
> [@tej-juwekar](https://github.com/tej-juwekar)) from a fresh Claude Code
> session on either machine, after cloning the pushed repo. Anyone
> resuming should: clone, run the README's Setup steps (including
> `git config core.hooksPath .githooks`), then start at Task 2 and follow
> superpowers:subagent-driven-development or superpowers:executing-plans
> task-by-task as normal — there is no special handoff state beyond what's
> already committed.

**Goal:** Stand up the `planning-intelligence` repo as the generalized multi-council Irish planning-data foundation: repo scaffold, canonical Postgres/PostGIS schema, Galway City (ported from duffy) and Galway County (built fresh) ingestion, the `/onboard-council` skill + two subagents, and GitHub hosting.

**Architecture:** Pipeline stages (`discover` → `acquire` → `extract` → `normalize` → `resolve` → `publish`) per source region, writing into a canonical `applications` / `application_events` schema. Parsers are organized by family (`pdf_table_lines` first). Market layering (`GALWAY_CITY` / `GALWAY_METRO` / `GALWAY_COUNTY`) is derived from source region + geometry, computed in `src/markets/`.

**Tech Stack:** Python 3.11, SQLAlchemy + Alembic, Pydantic v2, PostgreSQL 16 + PostGIS (via `docker-compose.yml`), `pdfplumber`, `requests`, `beautifulsoup4` (County HTML scraping), `pytest`.

## Global Constraints

- Python 3.11, `pyproject.toml` is the single source of dependency truth (spec §2).
- Postgres + PostGIS chosen over SQLite — `site_geometry` and market-derivation polygon queries need real GIS (spec §2).
- Raw downloads under `data/<county>/<region>/temp/` are disposable, `.gitignore`d — not a system of record (spec §3.1). Provenance is preserved via `source_file` + `raw_payload_json` on `applications`.
- Migrations under `src/core/db/migrations/`, naming `<revision>_<verb>_<subject>.py`, one migration per logical change, never hand-edit an applied migration (spec §2).
- Natural key for application dedup: `planning_authority + application_ref` (spec §4, dev-plan §6.5).
- `src/markets/galway/metro.py` ships as an explicit TODO-comment stub, not a working implementation (spec §3, §10).
- Out of scope: RAG/chat layer (`chat_app.py`, `rag_engine.py`, `embedder.py`, `query_engine.py`, `report_generator.py` from duffy), any council beyond Galway City/County, CI/CD, branch protection automation (spec §10, §8).
- Manual-only (never automate): collaborator addition, branch protection enablement (spec §9) — these stay as README-documented `gh`/web-UI steps for the human.

---

## Task 1: Repo Scaffold — Directory Tree, Config Files, Docs Copy

**Files:**
- Create: `pyproject.toml`
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `README.md`
- Create: `config/settings.py`
- Create: `config/logging.yaml`
- Create: `docs/foundation-development-plan.md` (copied from `/Users/akshitharsola/Documents/AiAgentic/Files/foundation-development-plan.md`)
- Create: `docs/strategy-report.md` (copied from `/Users/akshitharsola/Documents/AiAgentic/Files/cgpt-deep-research-report.md`)
- Create: `docs/source-inventory.md`
- Create: `docs/schema.md`
- Create: `docs/market-layering.md`
- Create: `CLAUDE.md` (project-level graphify convention for collaborators)
- Create: `.githooks/pre-commit` (auto-runs `graphify update .` and stages `graphify-out/` before every commit, on any contributor's machine)
- Create: `scripts/scaffold_tree.py` (cross-platform directory/`.gitkeep`/`__init__.py` scaffolder — macOS, Linux, and Windows)
- Create: directory placeholders (`.gitkeep`) for: `config/galway/`, `data/galway/city/temp/`, `data/galway/county/temp/`, `src/core/models/`, `src/core/db/migrations/`, `src/core/schemas/`, `src/core/normalization/`, `src/core/lifecycle/`, `src/core/geo/`, `src/parsers/pdf_lines/`, `src/parsers/pdf_text_fallback/`, `src/parsers/docx_state_machine/`, `src/parsers/pdf_ocr/`, `src/sources/base/`, `src/sources/galway/city/`, `src/sources/galway/county/`, `src/pipelines/`, `src/markets/galway/`, `src/services/`, `src/monitoring/`, `tests/fixtures/`, `tests/unit/`, `tests/integration/`, `tests/regression/`, `.claude/skills/onboard-council/`, `.claude/agents/`
- Create: `src/__init__.py` and `__init__.py` in every `src/` subpackage listed above

**Interfaces:**
- Produces: `config.settings` module importable as `from config.settings import get_database_url, DATA_DIR` — later tasks (Task 4 DB session, Task 6 scraper) import from here.
- Produces: repo directory tree that every subsequent task's file paths assume exists.

- [ ] **Step 1: Create the directory tree with `__init__.py` placeholders**

The original plan used bash-only `mkdir -p` / `touch` / `find -exec`, which
don't run on native Windows (PowerShell/cmd.exe). Since this repo will be
cloned and worked on by two people — one of whom may be on Windows — this
step uses a small cross-platform Python script instead. Run it once with
plain `python3` (any OS with Python 3.11 installed, no shell-specific
syntax):

```python
# scripts/scaffold_tree.py — run once: `python3 scripts/scaffold_tree.py`
# Cross-platform (macOS/Linux/Windows) replacement for `mkdir -p` + `touch`.
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DIRS = [
    "config/galway",
    "data/galway/city/temp",
    "data/galway/county/temp",
    "src/core/models",
    "src/core/db/migrations",
    "src/core/schemas",
    "src/core/normalization",
    "src/core/lifecycle",
    "src/core/geo",
    "src/parsers/pdf_lines",
    "src/parsers/pdf_text_fallback",
    "src/parsers/docx_state_machine",
    "src/parsers/pdf_ocr",
    "src/sources/base",
    "src/sources/galway/city",
    "src/sources/galway/county",
    "src/pipelines",
    "src/markets/galway",
    "src/services",
    "src/monitoring",
    "tests/fixtures",
    "tests/unit/parsers",
    "tests/integration",
    "tests/regression",
    ".claude/skills/onboard-council",
    ".claude/agents",
]

INIT_FILES = [
    "src/__init__.py",
    "src/core/__init__.py",
    "src/core/models/__init__.py",
    "src/core/db/__init__.py",
    "src/core/schemas/__init__.py",
    "src/core/normalization/__init__.py",
    "src/core/lifecycle/__init__.py",
    "src/core/geo/__init__.py",
    "src/parsers/__init__.py",
    "src/parsers/pdf_lines/__init__.py",
    "src/parsers/pdf_text_fallback/__init__.py",
    "src/parsers/docx_state_machine/__init__.py",
    "src/parsers/pdf_ocr/__init__.py",
    "src/sources/__init__.py",
    "src/sources/base/__init__.py",
    "src/sources/galway/__init__.py",
    "src/sources/galway/city/__init__.py",
    "src/sources/galway/county/__init__.py",
    "src/pipelines/__init__.py",
    "src/markets/__init__.py",
    "src/markets/galway/__init__.py",
    "src/services/__init__.py",
    "src/monitoring/__init__.py",
    "config/__init__.py",
]


def main() -> None:
    for rel in DIRS:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)

    for rel in INIT_FILES:
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)

    for tests_dir in (ROOT / "tests").rglob("*"):
        if tests_dir.is_dir():
            (tests_dir / ".gitkeep").touch(exist_ok=True)

    for temp_dir in (ROOT / "data").rglob("temp"):
        if temp_dir.is_dir():
            (temp_dir / ".gitkeep").touch(exist_ok=True)

    print("Scaffold tree created.")


if __name__ == "__main__":
    main()
```

```bash
mkdir -p scripts
python3 scripts/scaffold_tree.py
```

(On Windows: `python scripts\scaffold_tree.py` from a regular terminal —
no Git Bash required for this step, since it's pure Python.)

This script is a one-time scaffold tool, not part of the application — it
stays in the repo under `scripts/` so either collaborator (or a fresh
re-clone) can regenerate the tree structure identically on any OS.

- [ ] **Step 2: Write `pyproject.toml`**

```toml
[project]
name = "planning-intelligence"
version = "0.1.0"
description = "Multi-council Irish planning-data ingestion platform"
requires-python = ">=3.11"
dependencies = [
    "sqlalchemy>=2.0",
    "alembic>=1.13",
    "pydantic>=2.6",
    "psycopg2-binary>=2.9",
    "geoalchemy2>=0.14",
    "pdfplumber>=0.11",
    "requests>=2.31",
    "beautifulsoup4>=4.12",
    "python-dotenv>=1.0",
    "PyYAML>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 3: Write `docker-compose.yml`**

```yaml
services:
  postgres:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES_USER: planning
      POSTGRES_PASSWORD: planning
      POSTGRES_DB: planning_intelligence
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

- [ ] **Step 4: Write `.env.example`**

```bash
DATABASE_URL=postgresql://planning:planning@localhost:5432/planning_intelligence
DATA_DIR=./data
LOG_LEVEL=INFO
```

- [ ] **Step 5: Write `.gitignore`**

```gitignore
.venv/
__pycache__/
*.pyc
.env
data/*/*/temp/*
!data/*/*/temp/.gitkeep
*.egg-info/
.pytest_cache/
.coverage
.DS_Store
```

`graphify-out/` is intentionally **not** listed here — it is committed so
collaborators get the knowledge graph on clone (see Step 10's `CLAUDE.md`
and Step 11's README "Knowledge graph" section).

- [ ] **Step 6: Write `config/settings.py`**

```python
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set — copy .env.example to .env")
    return url
```

- [ ] **Step 7: Write `config/logging.yaml`**

```yaml
version: 1
formatters:
  default:
    format: "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
handlers:
  console:
    class: logging.StreamHandler
    formatter: default
    stream: ext://sys.stdout
root:
  level: INFO
  handlers: [console]
```

- [ ] **Step 8: Copy reference docs into the repo**

```bash
cp /Users/akshitharsola/Documents/AiAgentic/Files/foundation-development-plan.md docs/foundation-development-plan.md
cp /Users/akshitharsola/Documents/AiAgentic/Files/cgpt-deep-research-report.md docs/strategy-report.md
```

- [ ] **Step 9: Write stub `docs/source-inventory.md`, `docs/schema.md`, `docs/market-layering.md`**

```markdown
<!-- docs/source-inventory.md -->
# Source Inventory

Per-council/region planning data sources: URLs, file formats, update cadence.
Populated incrementally — Galway City and County entries added in Task 6/9;
every council after that is appended by the `/onboard-council` skill's
`source-onboarding` subagent.

## Galway City

(added in Task 6)

## Galway County

(added in Task 9)
```

```markdown
<!-- docs/schema.md -->
# Canonical Schema

Describes the `applications` and `application_events` tables implemented in
`src/core/models/`. See Task 2 for the SQLAlchemy models and Pydantic mirrors.
```

```markdown
<!-- docs/market-layering.md -->
# Market Layering

City / Metro / County market-entity derivation rules. See `src/markets/galway/`
(Task 8) and the 2026-06-25 commuter-shed discussion for the Metro stub's
open questions.
```

- [ ] **Step 10: Write `CLAUDE.md`**

```markdown
## graphify

This project has a graphify knowledge graph at `graphify-out/`. It is
committed to the repo so every collaborator gets it on clone — no local
setup needed to browse the architecture.

Rules:
- Before answering architecture or codebase questions, read
  `graphify-out/GRAPH_REPORT.md` for god nodes and community structure.
- If `graphify-out/wiki/index.md` exists, navigate it instead of reading
  raw files.
- After modifying code files in this session, run `graphify update .` to
  keep the graph current (AST-only, no API cost) and commit the
  `graphify-out/` changes alongside your code changes in the same commit.
```

- [ ] **Step 11: Write `.githooks/pre-commit` and configure git to use it**

Relying on each collaborator's Claude Code session to remember the
`CLAUDE.md` graphify rule isn't reliable when two people on two machines
are both committing — a hook enforces it regardless of who or what tool
makes the commit.

```bash
#!/usr/bin/env bash
# .githooks/pre-commit
set -euo pipefail

if command -v graphify >/dev/null 2>&1; then
    graphify update . || {
        echo "graphify update failed — see output above. Commit aborted." >&2
        exit 1
    }
    git add graphify-out/
else
    echo "Warning: graphify not installed on this machine — graphify-out/ may go stale." >&2
fi
```

```bash
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
```

`core.hooksPath` is a local git config, not committed — each collaborator
must run `git config core.hooksPath .githooks` once after cloning. Add this
to the README setup steps (Step 12) so it isn't missed.

**Windows note:** `chmod +x` is a no-op on Windows filesystems (NTFS has
no POSIX exec bit) — skip that line on Windows, it isn't needed there.
Git for Windows ships Git Bash, and `core.hooksPath` invokes hooks through
it automatically, so the `#!/usr/bin/env bash` script above runs as-is on
Windows with no changes — just run `git config core.hooksPath .githooks`
(no `chmod`). The only requirement is that `graphify` itself is on PATH
on that machine; if not, the hook's `command -v graphify` check prints
the warning and lets the commit proceed rather than failing it.

- [ ] **Step 12: Write `README.md`**

```markdown
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

## Running tests

```bash
pytest
```

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
```

- [ ] **Step 13: Verify the tree**

```bash
find . -path ./.git -prune -o -type f -print | sort
```

- [ ] **Step 14: Run `/graphify` and commit everything, including the generated graph**

```bash
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
git add -A
git commit -m "scaffold: repo layout, pyproject, docker-compose, docs copies, CLAUDE.md, pre-commit hook"
```

The `git commit` above triggers `.githooks/pre-commit`, which runs
`graphify update .` — but `graphify-out/` doesn't exist yet on the first
commit, so the hook's `graphify update .` call has nothing to update and
the commit proceeds with just the scaffold files. Now, in Claude Code, run
`/graphify .` from the repo root to generate `graphify-out/` (HTML graph,
JSON, `GRAPH_REPORT.md`) for the first time. Once it finishes:

```bash
git add graphify-out/
git commit -m "docs: add initial graphify knowledge graph for repo scaffold"
```

From here on, every commit on either collaborator's machine automatically
re-runs `graphify update .` and stages `graphify-out/` via the pre-commit
hook (Step 11) — no manual `graphify update .` step is needed at the end
of Tasks 2-12, as long as each collaborator has run
`git config core.hooksPath .githooks` once after cloning (README Setup
section, Step 12).

Expected: `find` shows all files from Steps 1-10 with no unexpected extras; both commits succeed.

---

## Task 2: Canonical SQLAlchemy Models + Pydantic Schemas

**Files:**
- Create: `src/core/db/base.py`
- Create: `src/core/db/session.py`
- Create: `src/core/models/application.py`
- Create: `src/core/models/application_event.py`
- Create: `src/core/schemas/application.py`
- Create: `src/core/schemas/application_event.py`
- Test: `tests/unit/core/test_application_schema.py`
- Test: `tests/unit/core/test_application_event_schema.py`

**Interfaces:**
- Consumes: `config.settings.get_database_url` (Task 1, Step 6).
- Produces: `Application`, `ApplicationEvent` SQLAlchemy models (importable from `src.core.models.application` / `src.core.models.application_event`) — Task 3's Alembic migration autogenerates against `Base.metadata` from these. `ApplicationCreate` / `ApplicationEventCreate` Pydantic schemas (importable from `src.core.schemas.application` / `src.core.schemas.application_event`) — Task 7's `normalize.py` and Task 11's onboard-council parser-dev subagent, and any council's parser unit tests, validate raw rows against these.

- [ ] **Step 1: Write the failing schema test for `Application`**

```python
# tests/unit/core/test_application_schema.py
import pytest
from pydantic import ValidationError

from src.core.schemas.application import ApplicationCreate


def test_application_create_requires_natural_key():
    app = ApplicationCreate(
        planning_authority="Galway City Council",
        source_entity="GALWAY_CITY_COUNCIL",
        application_ref="24/1234",
        applicant_name="John Smith",
        development_description="Construction of extension at 19 Monivea Road",
        application_type="Permission",
        planning_status_current="Received",
        date_received="2026-03-02",
        source_system="Galway City Weekly Lists PDF",
        source_file="Weekly Lists - Planning Applications Received.pdf",
    )
    assert app.application_ref == "24/1234"
    assert app.market_entity is None


def test_application_create_rejects_missing_application_ref():
    with pytest.raises(ValidationError):
        ApplicationCreate(
            planning_authority="Galway City Council",
            source_entity="GALWAY_CITY_COUNCIL",
            applicant_name="John Smith",
            development_description="x",
            application_type="Permission",
            planning_status_current="Received",
            date_received="2026-03-02",
            source_system="Galway City Weekly Lists PDF",
            source_file="x.pdf",
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/core/test_application_schema.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.core.schemas.application'`

- [ ] **Step 3: Write `src/core/schemas/application.py`**

```python
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OtherRegulatoryFlags(BaseModel):
    ipc_licence: bool = False
    waste_licence: bool = False


class ApplicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Core
    planning_authority: str
    source_entity: str
    application_ref: str
    application_ref_type: Optional[str] = None
    applicant_name: str
    site_address: Optional[str] = None
    site_locality: Optional[str] = None
    site_county: Optional[str] = None
    site_geometry: Optional[str] = None  # WKT, parsed to geometry at the DB layer
    development_description: str
    application_type: str

    # Lifecycle and status
    planning_status_current: str
    status_event_type: Optional[str] = None
    date_received: date
    decision_due_date: Optional[date] = None
    decision_date: Optional[date] = None
    further_information_flag: bool = False
    protected_structure_flag: bool = False
    eia_eis_flag: bool = False
    other_regulatory_flags: OtherRegulatoryFlags = Field(default_factory=OtherRegulatoryFlags)

    # Provenance
    official_detail_url: Optional[str] = None
    official_documents_url: Optional[str] = None
    source_system: str
    source_file: str
    source_ingested_at: datetime = Field(default_factory=datetime.now)
    raw_payload_json: dict = Field(default_factory=dict)

    # Market layer
    market_entity: Optional[str] = None
    commuter_belt_flag: bool = False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/core/test_application_schema.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Write the failing test for `ApplicationEvent`**

```python
# tests/unit/core/test_application_event_schema.py
from src.core.schemas.application_event import ApplicationEventCreate


def test_application_event_create():
    event = ApplicationEventCreate(
        application_ref="24/1234",
        planning_authority="Galway City Council",
        event_type="APPLICATION_RECEIVED",
        event_date="2026-03-02",
        source_file="Weekly Lists - Planning Applications Received.pdf",
    )
    assert event.event_type == "APPLICATION_RECEIVED"
```

- [ ] **Step 6: Run test to verify it fails**

Run: `pytest tests/unit/core/test_application_event_schema.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.core.schemas.application_event'`

- [ ] **Step 7: Write `src/core/schemas/application_event.py`**

```python
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

EVENT_TYPES = {
    "APPLICATION_RECEIVED",
    "FURTHER_INFORMATION_REQUESTED",
    "FURTHER_INFORMATION_RECEIVED",
    "DECISION_GRANTED",
    "DECISION_REFUSED",
    "APPLICATION_WITHDRAWN",
    "APPLICATION_INVALID",
    "APPEAL_LODGED",
    "APPEAL_DECIDED",
}


class ApplicationEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application_ref: str
    planning_authority: str
    event_type: str
    event_date: date
    source_file: str
    raw_payload_json: dict = Field(default_factory=dict)
```

- [ ] **Step 8: Run both tests to verify they pass**

Run: `pytest tests/unit/core/ -v`
Expected: PASS (3 tests)

- [ ] **Step 9: Write `src/core/db/base.py`**

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

- [ ] **Step 10: Write `src/core/db/session.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import get_database_url

engine = create_engine(get_database_url())
SessionLocal = sessionmaker(bind=engine)
```

- [ ] **Step 11: Write `src/core/models/application.py`**

```python
import uuid
from datetime import date, datetime

from geoalchemy2 import Geometry
from sqlalchemy import JSON, Boolean, Date, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import Base


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Core
    planning_authority: Mapped[str] = mapped_column(String, nullable=False)
    source_entity: Mapped[str] = mapped_column(String, nullable=False)
    application_ref: Mapped[str] = mapped_column(String, nullable=False)
    application_ref_type: Mapped[str | None] = mapped_column(String, nullable=True)
    applicant_name: Mapped[str] = mapped_column(String, nullable=False)
    site_address: Mapped[str | None] = mapped_column(String, nullable=True)
    site_locality: Mapped[str | None] = mapped_column(String, nullable=True)
    site_county: Mapped[str | None] = mapped_column(String, nullable=True)
    site_geometry = mapped_column(Geometry(geometry_type="GEOMETRY", srid=4326), nullable=True)
    development_description: Mapped[str] = mapped_column(String, nullable=False)
    application_type: Mapped[str] = mapped_column(String, nullable=False)

    # Lifecycle and status
    planning_status_current: Mapped[str] = mapped_column(String, nullable=False)
    status_event_type: Mapped[str | None] = mapped_column(String, nullable=True)
    date_received: Mapped[date] = mapped_column(Date, nullable=False)
    decision_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    decision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    further_information_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    protected_structure_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    eia_eis_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    other_regulatory_flags: Mapped[dict] = mapped_column(JSON, default=dict)

    # Provenance
    official_detail_url: Mapped[str | None] = mapped_column(String, nullable=True)
    official_documents_url: Mapped[str | None] = mapped_column(String, nullable=True)
    source_system: Mapped[str] = mapped_column(String, nullable=False)
    source_file: Mapped[str] = mapped_column(String, nullable=False)
    source_ingested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    raw_payload_json: Mapped[dict] = mapped_column(JSON, default=dict)

    # Market layer
    market_entity: Mapped[str | None] = mapped_column(String, nullable=True)
    commuter_belt_flag: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        # Natural key per spec section 4 / dev-plan section 6.5
        {"sqlite_autoincrement": False},
    )
```

- [ ] **Step 12: Write `src/core/models/application_event.py`**

```python
import uuid
from datetime import date

from sqlalchemy import JSON, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import Base


class ApplicationEvent(Base):
    __tablename__ = "application_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False
    )
    application_ref: Mapped[str] = mapped_column(String, nullable=False)
    planning_authority: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_file: Mapped[str] = mapped_column(String, nullable=False)
    raw_payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
```

- [ ] **Step 13: Add a unique constraint test for the natural key**

```python
# tests/unit/core/test_application_natural_key.py
from sqlalchemy import UniqueConstraint

from src.core.models.application import Application


def test_application_has_natural_key_constraint():
    constraints = [
        c for c in Application.__table__.constraints
        if isinstance(c, UniqueConstraint)
    ]
    assert any(
        set(c.columns.keys()) == {"planning_authority", "application_ref"}
        for c in constraints
    )
```

- [ ] **Step 14: Run test to verify it fails**

Run: `pytest tests/unit/core/test_application_natural_key.py -v`
Expected: FAIL — `assert any(...)` is False (no such constraint yet)

- [ ] **Step 15: Add the natural-key unique constraint to `Application`**

In `src/core/models/application.py`, replace the `__table_args__` line:

```python
    __table_args__ = (
        UniqueConstraint("planning_authority", "application_ref", name="uq_application_natural_key"),
    )
```

And add the import at the top:

```python
from sqlalchemy import JSON, Boolean, Date, DateTime, String, UniqueConstraint
```

- [ ] **Step 16: Run test to verify it passes**

Run: `pytest tests/unit/core/ -v`
Expected: PASS (4 tests)

- [ ] **Step 17: Commit**

```bash
git add src/core/ tests/unit/core/
git commit -m "feat: canonical Application/ApplicationEvent models and Pydantic schemas"
```

---

## Task 3: First Alembic Migration

**Files:**
- Create: `alembic.ini`
- Create: `src/core/db/migrations/env.py`
- Create: `src/core/db/migrations/script.py.mako`
- Create: `src/core/db/migrations/versions/0001_create_applications_and_events.py`
- Test: `tests/integration/test_migration_applies.py`

**Interfaces:**
- Consumes: `Base` (Task 2, Step 9), `Application` + `ApplicationEvent` models (Task 2, Steps 11-12), `get_database_url` (Task 1, Step 6).
- Produces: a running `applications` + `application_events` schema in the Postgres container — Task 7's `pipelines/publish.py` and future parser integration tests write through this schema.

- [ ] **Step 1: Write `alembic.ini`**

```ini
[alembic]
script_location = src/core/db/migrations
prepend_sys_path = .

[loggers]
keys = root,sqlalchemy,alembic

[logger_root]
level = WARNING
handlers = console
qualname =

[logger_sqlalchemy]
level = WARNING
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handlers]
keys = console

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatters]
keys = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 2: Write `src/core/db/migrations/env.py`**

```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import geoalchemy2  # noqa: F401 — registers Geometry type with Alembic's autogenerate renderer
from config.settings import get_database_url
from src.core.db.base import Base
from src.core.models import application, application_event  # noqa: F401 — registers models on Base.metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_database_url())
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 3: Write `src/core/db/migrations/script.py.mako`**

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 4: Start Postgres and generate the migration**

```bash
docker compose up -d
sleep 3
alembic revision --autogenerate -m "create applications and events"
```

Expected: a new file appears under `src/core/db/migrations/versions/` — rename it to `0001_create_applications_and_events.py` per the naming convention in Global Constraints.

```bash
mv src/core/db/migrations/versions/*_create_applications_and_events.py \
   src/core/db/migrations/versions/0001_create_applications_and_events.py
```

- [ ] **Step 5: Apply the migration**

```bash
alembic upgrade head
```

Expected: no errors; `applications` and `application_events` tables exist in Postgres.

- [ ] **Step 6: Write the integration test verifying the schema applied**

```python
# tests/integration/test_migration_applies.py
from sqlalchemy import inspect

from src.core.db.session import engine


def test_applications_table_exists():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "applications" in tables
    assert "application_events" in tables


def test_applications_has_natural_key_unique_constraint():
    inspector = inspect(engine)
    constraints = inspector.get_unique_constraints("applications")
    assert any(
        set(c["column_names"]) == {"planning_authority", "application_ref"}
        for c in constraints
    )
```

- [ ] **Step 7: Run the test to verify it passes**

Run: `pytest tests/integration/test_migration_applies.py -v`
Expected: PASS (2 tests) — requires `docker compose up -d` and `alembic upgrade head` to have run first.

- [ ] **Step 8: Commit**

```bash
git add alembic.ini src/core/db/migrations/ tests/integration/test_migration_applies.py
git commit -m "feat: first Alembic migration for applications/application_events schema"
```

---

## Task 4: Galway City Config + Discover Pipeline

**Files:**
- Create: `config/galway/city.yaml`
- Create: `src/sources/base/source.py`
- Create: `src/pipelines/discover.py`
- Test: `tests/unit/pipelines/test_discover_galway_city.py`

**Interfaces:**
- Consumes: nothing from earlier tasks (this is the first pipeline stage).
- Produces: `BaseSource` ABC (importable from `src.sources.base.source`) with `discover() -> list[dict]` — Task 5's `GalwayCityScraper` implements this. `load_region_config(path: Path) -> dict` (importable from `src.pipelines.discover`) — Task 5 and Task 9 both call this to read their respective `config/<county>/<region>.yaml`.

This folds duffy's `config.py` PDF_PATTERNS / month-folder logic and `folder_walker.py`'s week-folder discovery into config + a thin discover module, per spec section 5.1's "Reference only" row for `folder_walker.py`/`config.py`.

- [ ] **Step 1: Write the failing test for region config loading**

```python
# tests/unit/pipelines/test_discover_galway_city.py
from pathlib import Path

from src.pipelines.discover import load_region_config


def test_load_galway_city_config():
    config = load_region_config(Path("config/galway/city.yaml"))
    assert config["source_entity"] == "GALWAY_CITY_COUNCIL"
    assert config["planning_authority"] == "Galway City Council"
    assert "pdf_patterns" in config
    assert config["pdf_patterns"]["received"] == [
        "planning applications received",
        "received  applications",
        "received applications",
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/pipelines/test_discover_galway_city.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.pipelines.discover'`

- [ ] **Step 3: Write `config/galway/city.yaml`**

```yaml
source_entity: GALWAY_CITY_COUNCIL
planning_authority: Galway City Council
parser_family: pdf_table_lines
base_url: "https://files.galwaycity.ie/gccplanninglists/"
lookback_months: 3
pdf_patterns:
  received:
    - "planning applications received"
    - "received  applications"
    - "received applications"
  granted:
    - "planning applications granted"
  refused:
    - "planning applications refused"
  firvalidated:
    - "firvalidated"
    - "fir validated"
    - "first validated"
  invalid:
    - "invalid applications"
  further_recd:
    - "further information received"
  further_reqd:
    - "further information requested"
  section5:
    - "section 5"
  section96:
    - "section 96"
  finger_post:
    - "finger post"
  outdoor:
    - "outdoor furniture"
  scaffolding:
    - "scaffolding"
  telecomms:
    - "telecommunications"
column_map:
  "file number": file_number
  "file no": file_number
  "applicants name": applicant
  "applicant name": applicant
  "applicant's name": applicant
  "app. type": app_type
  "app type": app_type
  "type": app_type
  "date received": date_received
  "development description and location": description
  "development description": description
  "description": description
  "eis recd.": eis
  "eis recd": eis
  "eis": eis
  "prot. stru": protected_structure
  "prot stru": protected_structure
  "protected structure": protected_structure
  "ipc lic.": ipc_licence
  "ipc lic": ipc_licence
  "waste lic.": waste_licence
  "waste lic": waste_licence
  "m.o. date": mo_date
  "m.o date": mo_date
  "mo date": mo_date
  "m.o. number": mo_number
  "m.o number": mo_number
  "mo number": mo_number
  "certificate number": cert_number
  "cert. no.": cert_number
  "decision": decision
  "date of decision": decision_date
```

- [ ] **Step 4: Write `src/pipelines/discover.py`**

```python
from pathlib import Path

import yaml


def load_region_config(path: Path) -> dict:
    """Load a `config/<county>/<region>.yaml` region config file."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/unit/pipelines/test_discover_galway_city.py -v`
Expected: PASS (1 test)

- [ ] **Step 6: Write `src/sources/base/source.py`**

```python
from abc import ABC, abstractmethod
from pathlib import Path


class BaseSource(ABC):
    """Interface every region's source module implements."""

    def __init__(self, region_config: dict, temp_dir: Path):
        self.region_config = region_config
        self.temp_dir = temp_dir

    @abstractmethod
    def discover(self) -> list[dict]:
        """Return a list of dicts describing available remote items
        (e.g. PDF links), not yet downloaded. Shape is source-specific
        but must include at minimum: 'filename' and a way to fetch it
        (e.g. 'url')."""
        raise NotImplementedError

    @abstractmethod
    def acquire(self, items: list[dict]) -> list[Path]:
        """Download the given items into self.temp_dir, return local paths."""
        raise NotImplementedError
```

- [ ] **Step 7: Commit**

```bash
git add config/galway/city.yaml src/sources/base/source.py src/pipelines/discover.py tests/unit/pipelines/test_discover_galway_city.py
git commit -m "feat: Galway City region config and discover/base-source interfaces"
```

---

## Task 5: Galway City Scraper Port (filegator API)

**Files:**
- Create: `src/sources/galway/city/scraper.py`
- Test: `tests/unit/sources/test_galway_city_scraper.py`

**Interfaces:**
- Consumes: `BaseSource` (Task 4, Step 6), `load_region_config` (Task 4, Step 4).
- Produces: `GalwayCityScraper.discover() -> list[dict]` where each dict has keys `url`, `filename`, `year`, `month_num`, `month_name`, `week_range` (same shape as duffy's `scraper.py::_discover_pdf_links`) — Task 6's PDF parser consumes the downloaded files by filename pattern, not this dict shape directly, but future onboarded regions' parser unit test fixtures (via Task 11's `/onboard-council` skill) are named following this `year/month_name/week_range/filename` convention.

Ports duffy's `scraper.py` (413 lines) almost directly — same filegator REST API mechanics (auth → list dir → download), same week-name normalization regex — retargeted to write into `temp_dir` instead of `DUFFY_ROOT`, and reading patterns from `region_config["pdf_patterns"]` instead of the module-level `KNOWN_PDF_SUBSTRINGS` constant.

- [ ] **Step 1: Write the failing test for week-name normalization**

```python
# tests/unit/sources/test_galway_city_scraper.py
from src.sources.galway.city.scraper import GalwayCityScraper


def test_normalise_week_handles_dot_date_ranges():
    assert GalwayCityScraper._normalise_week("02.03.2026-06.03.2026") == "2-6"
    assert GalwayCityScraper._normalise_week("02.02.2026 - 06.02.2026") == "2-6"
    assert GalwayCityScraper._normalise_week("05.01.2026 to 09.01.2026") == "5-9"
    assert GalwayCityScraper._normalise_week("2-6") == "2-6"


def test_build_local_path_uses_temp_dir(tmp_path):
    config = {"pdf_patterns": {}, "base_url": "https://files.galwaycity.ie/gccplanninglists/"}
    scraper = GalwayCityScraper(region_config=config, temp_dir=tmp_path)
    link = {
        "filename": "Weekly Lists - Planning Applications Received.pdf",
        "year": 2026,
        "month_name": "March",
        "week_range": "2-6",
    }
    path = scraper._build_local_path(link)
    assert path == tmp_path / "2026" / "March" / "2-6" / link["filename"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/sources/test_galway_city_scraper.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.sources.galway.city.scraper'`

- [ ] **Step 3: Write `src/sources/galway/city/scraper.py`**

```python
"""
Galway City Council weekly planning lists scraper.

Ported from duffy's scraper.py: hits the filegator REST API behind
files.galwaycity.ie directly with three plain HTTP calls
(auth -> list dir -> download). No browser automation needed.
"""

import base64
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

import requests

from src.sources.base.source import BaseSource

logger = logging.getLogger(__name__)

MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}


class GalwayCityScraper(BaseSource):
    def discover(self) -> list[dict]:
        lookback_months = self.region_config.get("lookback_months", 3)
        cutoff = datetime.today() - timedelta(days=lookback_months * 31)

        sess = self._auth_session()
        links: list[dict] = []
        base_url = self.region_config["base_url"]
        pdf_patterns = self.region_config["pdf_patterns"]
        known_substrings = [s for patterns in pdf_patterns.values() for s in patterns]

        for year_item in self._getdir(sess, "/"):
            if year_item["type"] != "dir" or not re.fullmatch(r"20\d{2}", year_item["name"]):
                continue
            year = int(year_item["name"])

            for month_item in self._getdir(sess, year_item["path"]):
                if month_item["type"] != "dir":
                    continue
                mk = month_item["name"].strip().lower().split()[0]
                if mk not in MONTH_NAMES:
                    continue
                month_num = MONTH_NAMES[mk]
                if datetime(year, month_num, 1) < cutoff:
                    continue
                month_display = mk.capitalize()

                for week_item in self._getdir(sess, month_item["path"]):
                    if week_item["type"] != "dir":
                        continue
                    week_range = self._normalise_week(week_item["name"])

                    for file_item in self._getdir(sess, week_item["path"]):
                        if file_item["type"] != "file":
                            continue
                        filename = file_item["name"]
                        if not filename.lower().endswith(".pdf"):
                            continue
                        if not any(s in filename.lower() for s in known_substrings):
                            continue
                        links.append({
                            "url": self._make_dl_url(base_url, file_item["path"]),
                            "filename": filename,
                            "year": year,
                            "month_num": month_num,
                            "month_name": month_display,
                            "week_range": week_range,
                        })
        return links

    def acquire(self, items: list[dict]) -> list[Path]:
        sess = self._auth_session()
        saved: list[Path] = []
        for link in items:
            local_path = self._build_local_path(link)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            r = sess.get(link["url"], timeout=60)
            r.raise_for_status()
            if r.content[:4] == b"%PDF":
                local_path.write_bytes(r.content)
                saved.append(local_path)
            else:
                logger.error(f"Response for {link['filename']} is not a PDF")
        return saved

    def _build_local_path(self, link: dict) -> Path:
        return (
            self.temp_dir
            / str(link["year"])
            / link["month_name"]
            / link["week_range"]
            / link["filename"]
        )

    def _auth_session(self) -> requests.Session:
        base_url = self.region_config["base_url"]
        sess = requests.Session()
        sess.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "X-Requested-With": "XMLHttpRequest",
            "Referer": base_url,
        })
        r = sess.get(base_url + "?r=/getuser", timeout=20)
        r.raise_for_status()
        token = r.headers.get("X-CSRF-Token") or r.headers.get("x-csrf-token")
        if not token:
            raise ValueError("No CSRF token in /getuser response — API may have changed.")
        sess.headers["x-csrf-token"] = token
        sess.headers["Content-Type"] = "application/json"
        return sess

    def _getdir(self, sess: requests.Session, path: str) -> list[dict]:
        base_url = self.region_config["base_url"]
        r = sess.post(base_url + "?r=/getdir", json={"dir": path}, timeout=20)
        r.raise_for_status()
        return [f for f in r.json()["data"]["files"] if f["type"] != "back"]

    @staticmethod
    def _make_dl_url(base_url: str, file_path: str) -> str:
        b64 = base64.b64encode(file_path.encode()).decode()
        return base_url + "?r=/download&path=" + quote(b64, safe="")

    @staticmethod
    def _normalise_week(server_name: str) -> str:
        s = server_name.strip()
        m = re.match(
            r"(\d{2})\.(\d{2})\.(\d{4})\s*(?:-+|to)\s*(\d{2})\.(\d{2})\.(\d{4})",
            s, re.IGNORECASE
        )
        if m:
            return f"{int(m.group(1))}-{int(m.group(4))}"
        return s
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/sources/test_galway_city_scraper.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add src/sources/galway/city/scraper.py tests/unit/sources/test_galway_city_scraper.py
git commit -m "feat: port Galway City filegator scraper from duffy"
```

---

## Task 6: Galway City PDF Parser Port (`pdf_table_lines`)

**Files:**
- Create: `src/parsers/pdf_lines/galway_city.py`
- Test: `tests/unit/parsers/test_galway_city_pdf_lines.py`

**Interfaces:**
- Consumes: `column_map` from `config/galway/city.yaml` (Task 4, Step 3).
- Produces: `extract_planning_table(pdf_path: Path, column_map: dict) -> list[dict]` — Task 7's `normalize.py` calls this per-PDF and receives raw row dicts keyed by the values in `column_map` (e.g. `file_number`, `applicant`, `description`).

Ports duffy's `pdf_extractor.py` (254 lines) directly — same pdfplumber lines-then-text-fallback strategy, same header detection, same boilerplate filtering — with `COLUMN_MAP` now an injected parameter instead of a module-level import from `config.py`.

- [ ] **Step 1: Write the failing test using a synthetic table (no real PDF needed yet)**

```python
# tests/unit/parsers/test_galway_city_pdf_lines.py
from src.parsers.pdf_lines.galway_city import _map_column, _normalise_rows, _is_boilerplate

COLUMN_MAP = {
    "file number": "file_number",
    "applicants name": "applicant",
    "app. type": "app_type",
    "date received": "date_received",
    "development description and location": "description",
    "eis recd.": "eis",
}


def test_map_column_exact_match():
    assert _map_column("File Number", COLUMN_MAP) == "file_number"


def test_map_column_partial_match():
    assert _map_column("EIS Recd. Extra", COLUMN_MAP) == "eis"


def test_map_column_fallback_slug():
    assert _map_column("Some New Field!", COLUMN_MAP) == "some_new_field"


def test_normalise_rows_skips_boilerplate():
    raw_rows = [
        ["File Number", "Applicants Name", "App. Type", "Date Received",
         "Development Description and Location", "EIS Recd."],
        ["24/1234", "John Smith", "P", "02/03/2026",
         "Construction of extension at 19 Monivea Road", "N"],
        ["", "Section 34 of the Planning Acts", "", "", "", ""],
    ]
    records = _normalise_rows(raw_rows, COLUMN_MAP)
    assert len(records) == 1
    assert records[0]["file_number"] == "24/1234"


def test_is_boilerplate_detects_legal_notice():
    assert _is_boilerplate("Section 34 of the Planning Acts applies")
    assert not _is_boilerplate("Construction of extension at 19 Monivea Road")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/parsers/test_galway_city_pdf_lines.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.parsers.pdf_lines.galway_city'`

- [ ] **Step 3: Write `src/parsers/pdf_lines/galway_city.py`**

```python
"""
Galway City weekly-list PDF parser — first concrete implementation of the
pdf_table_lines parser family. Ported from duffy's pdf_extractor.py.
"""

import logging
import re
from pathlib import Path
from typing import Optional

import pdfplumber

logger = logging.getLogger(__name__)

_SETTINGS_LINES = {
    "vertical_strategy": "lines",
    "horizontal_strategy": "lines",
    "snap_tolerance": 5,
    "join_tolerance": 3,
    "edge_min_length": 10,
    "min_words_vertical": 1,
}
_SETTINGS_TEXT = {
    "vertical_strategy": "text",
    "horizontal_strategy": "lines",
    "snap_tolerance": 5,
    "join_tolerance": 3,
}

_BOILERPLATE_FRAGMENTS = [
    "section 34 of",
    "data protection act",
    "personal details of",
    "freedom of information",
    "g a p p l i c a t i o n",
    "ceived from",
    "may be granted or refused",
    "cts 1988",
    "a p p l i c a t i o n s",
]

_HEADER_FRAGMENTS = [
    "file", "applicant", "app", "date", "description",
    "location", "eis", "prot", "ipc", "waste", "decision",
    "cert", "m.o", "number", "type",
]


def extract_planning_table(pdf_path: Path, column_map: dict) -> list[dict]:
    """Open a PDF and extract all table rows as a list of dicts keyed by
    column_map's values. Returns [] if extraction yields nothing useful."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_rows = _extract_rows(pdf, _SETTINGS_LINES)
            if not all_rows:
                all_rows = _extract_rows(pdf, _SETTINGS_TEXT)
    except Exception as exc:
        logger.error(f"Failed to open/parse {pdf_path}: {exc}")
        return []

    if not all_rows:
        logger.warning(f"No table data extracted from {pdf_path.name}")
        return []

    return _normalise_rows(all_rows, column_map)


def _extract_rows(pdf: "pdfplumber.PDF", settings: dict) -> list[list]:
    all_rows: list[list] = []
    header: Optional[list] = None

    for page in pdf.pages:
        tables = page.extract_tables(table_settings=settings)
        for table in tables or []:
            if not table:
                continue
            rows = [_clean_cells(row) for row in table if row]
            if header is None:
                for i, row in enumerate(rows):
                    if _looks_like_header(row):
                        header = row
                        all_rows.extend(rows[i:])
                        break
                else:
                    all_rows.extend(rows)
            else:
                for row in rows:
                    if not _is_duplicate_header(row, header):
                        all_rows.append(row)
    return all_rows


def _clean_cells(row: list) -> list:
    cleaned = []
    for cell in row:
        cleaned.append("" if cell is None else re.sub(r"\s+", " ", str(cell)).strip())
    return cleaned


def _looks_like_header(row: list) -> bool:
    text = " ".join(str(c).lower() for c in row if c)
    hits = sum(1 for frag in _HEADER_FRAGMENTS if frag in text)
    return hits >= 2


def _is_duplicate_header(row: list, header: list) -> bool:
    if len(row) != len(header):
        return False
    return all(_norm(a) == _norm(b) for a, b in zip(row, header))


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s).lower()).strip()


def _normalise_rows(raw_rows: list[list], column_map: dict) -> list[dict]:
    if not raw_rows:
        return []

    header_idx = None
    for i, row in enumerate(raw_rows):
        if _looks_like_header(row):
            header_idx = i
            break
    if header_idx is None:
        logger.warning("Could not identify header row; skipping normalisation.")
        return []

    raw_header = raw_rows[header_idx]
    mapped_keys = [_map_column(h, column_map) for h in raw_header]

    records: list[dict] = []
    for row in raw_rows[header_idx + 1:]:
        if all(c == "" for c in row):
            continue
        row = (row + [""] * len(mapped_keys))[: len(mapped_keys)]
        record = {k: v for k, v in zip(mapped_keys, row)}
        if record.get("file_number") or record.get("description"):
            if any(_is_boilerplate(record.get(f, "")) for f in
                   ("file_number", "applicant", "description")):
                continue
            records.append(record)
    return records


def _is_boilerplate(text: str) -> bool:
    t = text.lower()
    return any(f in t for f in _BOILERPLATE_FRAGMENTS)


def _map_column(raw: str, column_map: dict) -> str:
    key = re.sub(r"\s+", " ", raw.lower()).strip().rstrip(".")
    if key in column_map:
        return column_map[key]
    for k, v in column_map.items():
        if k in key or key in k:
            return v
    return re.sub(r"[^a-z0-9]+", "_", key).strip("_")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/parsers/test_galway_city_pdf_lines.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add src/parsers/pdf_lines/galway_city.py tests/unit/parsers/test_galway_city_pdf_lines.py
git commit -m "feat: port Galway City pdf_table_lines parser from duffy"
```

---

## Task 7: Normalize + Resolve + Publish Pipeline (Galway City)

**Files:**
- Create: `src/core/normalization/galway_city.py`
- Create: `src/core/normalization/location.py`
- Create: `src/pipelines/normalize.py`
- Create: `src/pipelines/resolve.py`
- Create: `src/pipelines/publish.py`
- Test: `tests/unit/pipelines/test_normalize_galway_city.py`
- Test: `tests/unit/normalization/test_location.py`

**Interfaces:**
- Consumes: raw row dicts from `extract_planning_table` (Task 6), `ApplicationCreate` / `ApplicationEventCreate` (Task 2, Steps 3 and 7), `pdf_patterns` keys from `config/galway/city.yaml` (Task 4, Step 3) as the `source_type` → `event_type` mapping.
- Produces: `normalize_row(raw_row: dict, source_type: str, region_config: dict, source_file: str) -> ApplicationCreate` (importable from `src.pipelines.normalize`) — Task 11's `/onboard-council` skill workflow and any future region's normalize step follow this same signature. `extract_location(description: str) -> dict` (importable from `src.core.normalization.location`) with keys `area`, `address`, `eircode` — used by `normalize_row` to populate `site_locality`/`site_address`.

Ports the row-mapping intent of duffy's `data_processor.py` (PDF-type → event-type, flag parsing) and `location_extractor.py` (address/area/eircode extraction from `description`), retargeted from duffy's flat SQLite columns onto the canonical `ApplicationCreate` schema.

- [ ] **Step 1: Write the failing test for location extraction**

```python
# tests/unit/normalization/test_location.py
from src.core.normalization.location import extract_location


def test_extract_location_finds_eircode_and_area():
    desc = "Construction of extension at 19 Monivea Road Mervue Galway H91 TX20"
    loc = extract_location(desc)
    assert loc["eircode"] == "H91 TX20"
    assert loc["area"] == "Mervue"


def test_extract_location_handles_empty_description():
    assert extract_location("") == {"area": "", "address": "", "eircode": ""}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/normalization/test_location.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.core.normalization.location'`

- [ ] **Step 3: Write `src/core/normalization/location.py`**

```python
"""
Location extraction for Galway descriptions — ported from duffy's
location_extractor.py. Galway-specific area gazetteer; future regions
get their own gazetteer module under src/core/normalization/.
"""

import re

GALWAY_AREAS = [
    "salthill", "knocknacarra", "eyre square", "shop street", "quay street",
    "mainguard street", "dominick street", "abbeygate", "high street",
    "bohermore", "shantalla", "woodquay", "mervue", "doughiska",
    "ballybane", "ballymoneen", "castlegar", "tuam road", "headford road",
    "westside", "rahoon", "corrib", "moycullen road", "barna road",
    "upper salthill", "lower salthill", "renmore", "merlin park",
    "ballybrit", "briarhill", "parkmore", "coolough", "coolagh",
    "newcastle", "dangan", "upper newcastle", "lower newcastle",
    "bushypark", "menlo", "terryland", "wellpark", "kingston",
    "clybaun", "barna", "tuam road industrial", "briarhill business park",
    "galway technology park", "parkmore industrial",
    "galway city", "galway", "co. galway",
]

_EIRCODE_RE = re.compile(r"\bH\d{2}\s*[A-Z0-9]{4}\b", re.IGNORECASE)
_AT_RE = re.compile(
    r"\b(?:at|on lands at|located at|situate at|situate[d]? at|at lands at)\s+",
    re.IGNORECASE,
)


def extract_location(description: str) -> dict:
    if not description:
        return {"area": "", "address": "", "eircode": ""}
    return {
        "area": _extract_area(description),
        "address": _extract_address(description),
        "eircode": _extract_eircode(description),
    }


def _extract_eircode(text: str) -> str:
    m = _EIRCODE_RE.search(text)
    if m:
        raw = m.group(0).upper().replace(" ", "")
        return raw[:3] + " " + raw[3:]
    return ""


def _extract_area(text: str) -> str:
    text_lower = text.lower()
    for area in GALWAY_AREAS:
        if area in text_lower:
            idx = text_lower.find(area)
            return text[idx: idx + len(area)].title()
    return "Galway"


def _extract_address(text: str) -> str:
    matches = list(_AT_RE.finditer(text))
    if matches:
        candidate = text[matches[-1].end():].strip()
        candidate = re.split(r"[\n\r]", candidate)[0].strip()
        candidate = re.sub(r"\s+", " ", candidate)
        if 5 < len(candidate) < 200:
            return candidate
    parts = re.split(r"\.\s+", text)
    for part in reversed(parts):
        part = part.strip()
        if _looks_like_address(part):
            return re.sub(r"\s+", " ", part)[:200]
    return text.strip()[-120:].strip()


def _looks_like_address(text: str) -> bool:
    text_lower = text.lower()
    has_area = any(a in text_lower for a in GALWAY_AREAS)
    has_road = bool(re.search(
        r"\b(road|street|avenue|close|place|lane|drive|park|way|crescent|court|"
        r"rise|grove|view|heights|gardens|estate|terrace|row|square)\b",
        text_lower))
    short_enough = len(text) < 180
    starts_with_verb = bool(re.match(
        r"^(to |for |the |a |an |permission|construction|retention|demolition|"
        r"change|development|proposed|planning)", text_lower))
    return (has_area or has_road) and short_enough and not starts_with_verb
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/normalization/test_location.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Write the failing test for `normalize_row`**

```python
# tests/unit/pipelines/test_normalize_galway_city.py
from src.pipelines.normalize import normalize_row

REGION_CONFIG = {
    "source_entity": "GALWAY_CITY_COUNCIL",
    "planning_authority": "Galway City Council",
}


def test_normalize_row_received_maps_to_application_received_event():
    raw_row = {
        "file_number": "24/1234",
        "applicant": "John Smith",
        "app_type": "P",
        "date_received": "02/03/2026",
        "description": "Construction of extension at 19 Monivea Road Mervue Galway",
        "eis": "N",
        "protected_structure": "N",
    }
    app = normalize_row(raw_row, source_type="received", region_config=REGION_CONFIG,
                        source_file="Weekly Lists - Planning Applications Received.pdf")
    assert app.application_ref == "24/1234"
    assert app.planning_status_current == "Received"
    assert app.status_event_type == "APPLICATION_RECEIVED"
    assert app.site_locality == "Mervue"
    assert app.further_information_flag is False
    assert app.eia_eis_flag is False


def test_normalize_row_granted_sets_decision_fields():
    raw_row = {
        "file_number": "24/5678",
        "applicant": "Jane Doe",
        "app_type": "P",
        "description": "Retention of shed at Bohermore Galway",
        "mo_date": "10/03/2026",
        "mo_number": "456",
    }
    app = normalize_row(raw_row, source_type="granted", region_config=REGION_CONFIG,
                        source_file="Weekly Lists - Planning Applications Granted.pdf")
    assert app.planning_status_current == "Granted"
    assert app.status_event_type == "DECISION_GRANTED"
    assert app.decision_date is not None
```

- [ ] **Step 6: Run test to verify it fails**

Run: `pytest tests/unit/pipelines/test_normalize_galway_city.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.pipelines.normalize'`

- [ ] **Step 7: Write `src/pipelines/normalize.py`**

```python
"""
Maps a raw parser row (dict, source-specific keys) into the canonical
ApplicationCreate schema. source_type comes from the pdf_patterns key
the file matched (see config/galway/city.yaml).
"""

from datetime import datetime

from src.core.normalization.location import extract_location
from src.core.schemas.application import ApplicationCreate, OtherRegulatoryFlags

_SOURCE_TYPE_TO_STATUS = {
    "received": ("Received", "APPLICATION_RECEIVED"),
    "granted": ("Granted", "DECISION_GRANTED"),
    "refused": ("Refused", "DECISION_REFUSED"),
    "invalid": ("Invalid", "APPLICATION_INVALID"),
    "firvalidated": ("Received", "APPLICATION_RECEIVED"),
    "further_recd": ("Further Info", "FURTHER_INFORMATION_RECEIVED"),
    "further_reqd": ("Further Info", "FURTHER_INFORMATION_REQUESTED"),
}


def normalize_row(raw_row: dict, source_type: str, region_config: dict,
                   source_file: str) -> ApplicationCreate:
    status, event_type = _SOURCE_TYPE_TO_STATUS.get(source_type, ("Received", "APPLICATION_RECEIVED"))
    description = raw_row.get("description", "")
    location = extract_location(description)

    date_received = _parse_date(raw_row.get("date_received")) or datetime.now().date()
    decision_date = _parse_date(raw_row.get("mo_date"))

    return ApplicationCreate(
        planning_authority=region_config["planning_authority"],
        source_entity=region_config["source_entity"],
        application_ref=raw_row.get("file_number", ""),
        applicant_name=raw_row.get("applicant", ""),
        site_address=location["address"],
        site_locality=location["area"],
        site_county="Galway",
        development_description=description,
        application_type=_expand_app_type(raw_row.get("app_type", "")),
        planning_status_current=status,
        status_event_type=event_type,
        date_received=date_received,
        decision_date=decision_date,
        further_information_flag=source_type in ("further_recd", "further_reqd"),
        protected_structure_flag=_flag_yes(raw_row.get("protected_structure", "")),
        eia_eis_flag=_flag_yes(raw_row.get("eis", "")),
        other_regulatory_flags=OtherRegulatoryFlags(
            ipc_licence=_flag_yes(raw_row.get("ipc_licence", "")),
            waste_licence=_flag_yes(raw_row.get("waste_licence", "")),
        ),
        source_system="Galway City Weekly Lists PDF",
        source_file=source_file,
        raw_payload_json=raw_row,
    )


def _flag_yes(val: str) -> bool:
    return str(val).strip().upper() in ("Y", "YES", "TRUE", "1")


def _expand_app_type(code: str) -> str:
    return {"P": "Permission", "R": "Retention", "O": "Outline"}.get(code.strip().upper(), code or "Permission")


def _parse_date(value):
    if not value:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None
```

- [ ] **Step 8: Run test to verify it passes**

Run: `pytest tests/unit/pipelines/test_normalize_galway_city.py -v`
Expected: PASS (2 tests)

- [ ] **Step 9: Write `src/pipelines/resolve.py`**

```python
"""
Resolve stage: dedup applications by the natural key
(planning_authority + application_ref) and generate an ApplicationEvent
for each ingested row, per spec section 4 / dev-plan section 6.5.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.models.application import Application
from src.core.models.application_event import ApplicationEvent
from src.core.schemas.application import ApplicationCreate


def resolve_and_upsert(session: Session, app_create: ApplicationCreate) -> Application:
    existing = session.scalar(
        select(Application).where(
            Application.planning_authority == app_create.planning_authority,
            Application.application_ref == app_create.application_ref,
        )
    )

    if existing is None:
        application = Application(**app_create.model_dump(exclude={"site_geometry"}))
        session.add(application)
        session.flush()
    else:
        for field, value in app_create.model_dump(exclude={"site_geometry"}).items():
            setattr(existing, field, value)
        application = existing
        session.flush()

    event = ApplicationEvent(
        application_id=application.id,
        application_ref=app_create.application_ref,
        planning_authority=app_create.planning_authority,
        event_type=app_create.status_event_type or "APPLICATION_RECEIVED",
        event_date=app_create.date_received,
        source_file=app_create.source_file,
        raw_payload_json=app_create.raw_payload_json,
    )
    session.add(event)
    return application
```

- [ ] **Step 10: Write `src/pipelines/publish.py`**

```python
"""
Publish stage: commits the session and records ingestion metrics
(spec section 3 — src/monitoring/metrics.py, populated in Task 8).
"""

from sqlalchemy.orm import Session

from src.monitoring.metrics import record_ingestion_run


def publish(session: Session, region: str, rows_ingested: int, parse_errors: int) -> None:
    session.commit()
    record_ingestion_run(region=region, rows_ingested=rows_ingested, parse_errors=parse_errors)
```

- [ ] **Step 11: Write an integration test exercising normalize → resolve → publish end to end**

```python
# tests/integration/test_galway_city_pipeline_end_to_end.py
from src.core.db.session import SessionLocal
from src.pipelines.normalize import normalize_row
from src.pipelines.publish import publish
from src.pipelines.resolve import resolve_and_upsert

REGION_CONFIG = {
    "source_entity": "GALWAY_CITY_COUNCIL",
    "planning_authority": "Galway City Council",
}


def test_normalize_resolve_publish_roundtrip():
    raw_row = {
        "file_number": "TEST/0001",
        "applicant": "Test Applicant",
        "app_type": "P",
        "date_received": "02/03/2026",
        "description": "Test development at Bohermore Galway",
    }
    app_create = normalize_row(raw_row, source_type="received", region_config=REGION_CONFIG,
                               source_file="test.pdf")

    session = SessionLocal()
    try:
        application = resolve_and_upsert(session, app_create)
        publish(session, region="galway_city", rows_ingested=1, parse_errors=0)
        assert application.application_ref == "TEST/0001"
    finally:
        session.close()
```

- [ ] **Step 12: Run the integration test to verify it passes**

Run: `pytest tests/integration/test_galway_city_pipeline_end_to_end.py -v`
Expected: PASS (1 test) — requires Postgres running and migration applied (Task 3).

- [ ] **Step 13: Commit**

```bash
git add src/core/normalization/ src/pipelines/normalize.py src/pipelines/resolve.py src/pipelines/publish.py tests/unit/normalization/ tests/unit/pipelines/test_normalize_galway_city.py tests/integration/test_galway_city_pipeline_end_to_end.py
git commit -m "feat: normalize/resolve/publish pipeline for Galway City"
```

---

## Task 8: Markets (City/Metro/County) + Monitoring Metrics

**Note on ordering:** `src/pipelines/publish.py` (Task 7, Step 10) imports `record_ingestion_run` from this task's `src/monitoring/metrics.py`. Do this task's metrics module (Steps 1-4) before running Task 7 Step 12's integration test, or do Task 7 and Task 8 in the same working session before testing either's integration point.

**Files:**
- Create: `src/monitoring/metrics.py`
- Create: `src/markets/registry.py`
- Create: `src/markets/galway/city.py`
- Create: `src/markets/galway/metro.py`
- Create: `src/markets/galway/county.py`
- Test: `tests/unit/monitoring/test_metrics.py`
- Test: `tests/unit/markets/test_galway_markets.py`

**Interfaces:**
- Consumes: `Application` model (Task 2, Step 11) for market derivation's `planning_authority` field.
- Produces: `record_ingestion_run(region: str, rows_ingested: int, parse_errors: int) -> None` (importable from `src.monitoring.metrics`) — consumed by Task 7's `publish.py`. `derive_market_entities(application: Application) -> list[str]` (importable from `src.markets.registry`) — later services (`insight_service`, out of scope for this foundation) will call this; not yet wired into the publish pipeline in this pass since metro polygons are deferred (spec section 10).

- [ ] **Step 1: Write the failing test for metrics counters**

```python
# tests/unit/monitoring/test_metrics.py
from src.monitoring.metrics import get_metrics_snapshot, record_ingestion_run


def test_record_ingestion_run_increments_counters():
    record_ingestion_run(region="galway_city", rows_ingested=10, parse_errors=1)
    record_ingestion_run(region="galway_city", rows_ingested=5, parse_errors=0)
    snapshot = get_metrics_snapshot("galway_city")
    assert snapshot["rows_ingested_total"] == 15
    assert snapshot["parse_errors_total"] == 1
    assert snapshot["runs_total"] == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/monitoring/test_metrics.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.monitoring.metrics'`

- [ ] **Step 3: Write `src/monitoring/metrics.py`**

```python
"""
Minimal ingestion KPIs: rows ingested per run, per-region parser error
counts/rates. No dashboard/alerting in this foundation pass — just
structured counters that a later insight_service or external dashboard
can read. Per spec section 3.
"""

from collections import defaultdict

_counters: dict[str, dict[str, int]] = defaultdict(
    lambda: {"rows_ingested_total": 0, "parse_errors_total": 0, "runs_total": 0}
)


def record_ingestion_run(region: str, rows_ingested: int, parse_errors: int) -> None:
    bucket = _counters[region]
    bucket["rows_ingested_total"] += rows_ingested
    bucket["parse_errors_total"] += parse_errors
    bucket["runs_total"] += 1


def get_metrics_snapshot(region: str) -> dict[str, int]:
    return dict(_counters[region])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/monitoring/test_metrics.py -v`
Expected: PASS (1 test)

- [ ] **Step 5: Write the failing test for market derivation**

```python
# tests/unit/markets/test_galway_markets.py
from src.markets.registry import derive_market_entities


class FakeApplication:
    def __init__(self, planning_authority: str):
        self.planning_authority = planning_authority


def test_galway_city_council_maps_to_galway_city():
    app = FakeApplication("Galway City Council")
    assert derive_market_entities(app) == ["GALWAY_CITY"]


def test_galway_county_council_maps_to_galway_county():
    app = FakeApplication("Galway County Council")
    assert derive_market_entities(app) == ["GALWAY_COUNTY"]


def test_unknown_authority_maps_to_empty_list():
    app = FakeApplication("Some Other Council")
    assert derive_market_entities(app) == []
```

- [ ] **Step 6: Run test to verify it fails**

Run: `pytest tests/unit/markets/test_galway_markets.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.markets.registry'`

- [ ] **Step 7: Write `src/markets/galway/city.py`**

```python
def is_galway_city(planning_authority: str) -> bool:
    return planning_authority == "Galway City Council"
```

- [ ] **Step 8: Write `src/markets/galway/county.py`**

```python
def is_galway_county(planning_authority: str) -> bool:
    return planning_authority == "Galway County Council"
```

- [ ] **Step 9: Write `src/markets/galway/metro.py`**

```python
# TODO: commuter-belt polygons pending — see docs/source-inventory.md and
# the 2026-06-25 commuter-shed discussion (membership rule, POWCAR data,
# partition vs. shared-belt). Candidate source: Galway County's open-data
# ArcGIS portal.
#
# Once resolved, this module should expose:
#   def is_in_galway_metro(application) -> bool
# using application.site_geometry against the commuter-belt polygon(s).


def is_in_galway_metro(application) -> bool:
    raise NotImplementedError(
        "Galway Metro commuter-belt derivation is not implemented yet — "
        "see the TODO at the top of this file."
    )
```

- [ ] **Step 10: Write `src/markets/registry.py`**

```python
"""
Market-entity derivation registry. Metro derivation is deliberately
NOT wired in here yet — src/markets/galway/metro.py is a stub pending
the 2026-06-25 commuter-shed discussion's open questions (spec section 10).
"""

from src.markets.galway.city import is_galway_city
from src.markets.galway.county import is_galway_county


def derive_market_entities(application) -> list[str]:
    entities: list[str] = []
    if is_galway_city(application.planning_authority):
        entities.append("GALWAY_CITY")
    if is_galway_county(application.planning_authority):
        entities.append("GALWAY_COUNTY")
    return entities
```

- [ ] **Step 11: Run test to verify it passes**

Run: `pytest tests/unit/markets/test_galway_markets.py -v`
Expected: PASS (3 tests)

- [ ] **Step 12: Commit**

```bash
git add src/monitoring/metrics.py src/markets/ tests/unit/monitoring/ tests/unit/markets/
git commit -m "feat: ingestion metrics counters and Galway City/County market derivation"
```

---

## Task 9: Galway County — Built Fresh (HTML Scraper + Config)

**Files:**
- Create: `config/galway/county.yaml`
- Create: `src/sources/galway/county/scraper.py`
- Test: `tests/unit/sources/test_galway_county_scraper.py`

**Interfaces:**
- Consumes: `BaseSource` (Task 4, Step 6), `load_region_config` (Task 4, Step 4).
- Produces: `GalwayCountyScraper.discover() -> list[dict]` with keys `url`, `filename` — same minimal shape `BaseSource.discover()` requires, narrower than Galway City's dict because County's weekly-list page does not expose year/month/week folder structure the way the filegator API does (this is discovered by HTML scraping the listing page directly).

Per spec section 5.2: Galway County has no filegator-style API — duffy never built this integration, so it's new code, not a port. The weekly-list page is scraped with `requests` + `beautifulsoup4` for plain PDF download links. The ePlanning endpoint and ArcGIS layers are captured as config for future use but not yet implemented as acquirers (spec section 5.2 explicitly defers ePlanning/ArcGIS implementation past this foundation pass — only the weekly-list HTML scraper is built now).

- [ ] **Step 1: Write `config/galway/county.yaml`**

```yaml
source_entity: GALWAY_COUNTY_COUNCIL
planning_authority: Galway County Council
parser_family: pdf_table_lines
# Placeholder URL — source-onboarding subagent confirms the exact current
# URL and PDF link structure before parser-dev builds against real samples
# (spec section 5.2). Update this once confirmed.
weekly_list_url: "https://www.galwaycoco.ie/planning/weekly-lists/"
eplanning_endpoint: "https://eplanning.galwaycoco.ie/SearchListing/RECEIVED"
eplanning_window_days: 42
column_map:
  "file number": file_number
  "applicants name": applicant
  "applicant name": applicant
  "app. type": app_type
  "date received": date_received
  "development description and location": description
  "description": description
  "eis recd.": eis
  "protected structure": protected_structure
  "decision": decision
  "date of decision": decision_date
```

- [ ] **Step 2: Write the failing test for the County HTML scraper**

```python
# tests/unit/sources/test_galway_county_scraper.py
from src.sources.galway.county.scraper import GalwayCountyScraper

SAMPLE_HTML = """
<html><body>
  <div class="weekly-list">
    <a href="/files/weekly-2026-03-02-received.pdf">Applications Received 2-6 March 2026</a>
    <a href="/files/weekly-2026-03-02-granted.pdf">Applications Granted 2-6 March 2026</a>
    <a href="/about">About this page</a>
  </div>
</body></html>
"""


def test_parse_pdf_links_filters_to_pdfs_only():
    config = {"weekly_list_url": "https://www.galwaycoco.ie/planning/weekly-lists/"}
    scraper = GalwayCountyScraper(region_config=config, temp_dir="/tmp/unused")
    links = scraper._parse_pdf_links(SAMPLE_HTML)
    assert len(links) == 2
    assert links[0]["filename"] == "weekly-2026-03-02-received.pdf"
    assert links[0]["url"] == "https://www.galwaycoco.ie/files/weekly-2026-03-02-received.pdf"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/unit/sources/test_galway_county_scraper.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.sources.galway.county.scraper'`

- [ ] **Step 4: Write `src/sources/galway/county/scraper.py`**

```python
"""
Galway County Council weekly planning lists scraper — built fresh, no
duffy precedent (spec section 5.2). The weekly-list page is plain HTML
with PDF download links, unlike Galway City's filegator REST API.
"""

import logging
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from src.sources.base.source import BaseSource

logger = logging.getLogger(__name__)


class GalwayCountyScraper(BaseSource):
    def discover(self) -> list[dict]:
        url = self.region_config["weekly_list_url"]
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return self._parse_pdf_links(resp.text, base_url=url)

    def acquire(self, items: list[dict]) -> list[Path]:
        saved: list[Path] = []
        for link in items:
            local_path = Path(self.temp_dir) / link["filename"]
            local_path.parent.mkdir(parents=True, exist_ok=True)
            r = requests.get(link["url"], timeout=60)
            r.raise_for_status()
            if r.content[:4] == b"%PDF":
                local_path.write_bytes(r.content)
                saved.append(local_path)
            else:
                logger.error(f"Response for {link['filename']} is not a PDF")
        return saved

    def _parse_pdf_links(self, html: str, base_url: str | None = None) -> list[dict]:
        base_url = base_url or self.region_config["weekly_list_url"]
        soup = BeautifulSoup(html, "html.parser")
        links: list[dict] = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not href.lower().endswith(".pdf"):
                continue
            full_url = urljoin(base_url, href)
            filename = href.rsplit("/", 1)[-1]
            links.append({"url": full_url, "filename": filename})
        return links
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/unit/sources/test_galway_county_scraper.py -v`
Expected: PASS (1 test)

- [ ] **Step 6: Append the Galway County source entry to `docs/source-inventory.md`**

Edit `docs/source-inventory.md`, replacing the `## Galway County` section:

```markdown
## Galway County

- **Weekly-list page** (`config.galway.county.weekly_list_url`): plain HTML,
  PDF download links, scraped with `src/sources/galway/county/scraper.py`.
  URL needs confirmation by `source-onboarding` subagent before relying on
  it in production — placeholder per spec section 5.2.
- **ePlanning listing** (`config.galway.county.eplanning_endpoint`):
  `SearchListing/RECEIVED` etc., rolling 7-42 day window. Captured in config
  for future use; not yet implemented as an acquirer in this foundation pass.
- **ArcGIS open-data layers**: historical/geospatial backfill, referenced in
  dev-plan section 3.2. Not yet implemented.
- **Parser family**: `pdf_table_lines`, same family as Galway City pending
  confirmation against real sample PDFs (dev-plan section 3.2's "rich
  geospatial context" note implies similar tabular structure, but this is
  an assumption to verify, not a guarantee).
```

- [ ] **Step 7: Commit**

```bash
git add config/galway/county.yaml src/sources/galway/county/scraper.py tests/unit/sources/test_galway_county_scraper.py docs/source-inventory.md
git commit -m "feat: build Galway County HTML scraper and config from scratch"
```

---

## Task 10: Galway County Parser + Normalization

**Files:**
- Create: `src/parsers/pdf_lines/galway_county.py`
- Create: `src/core/normalization/galway_county.py`
- Test: `tests/unit/parsers/test_galway_county_pdf_lines.py`
- Test: `tests/unit/pipelines/test_normalize_galway_county.py`

**Interfaces:**
- Consumes: `column_map` from `config/galway/county.yaml` (Task 9, Step 1).
- Produces: `extract_planning_table(pdf_path: Path, column_map: dict) -> list[dict]` for County — same signature as Task 6's City parser, confirming the `pdf_table_lines` family assumption holds (per spec section 5.2, this is the `source-onboarding` subagent's first real job; this task builds the parser assuming the assumption holds, since duffy never had real County PDFs to test against — flag this explicitly to the human in Task 9/10's completion report per spec section 6, step 6, since it's marked there as something needing human review).

County's PDF structure is assumed similar to City's per dev-plan section 3.2. Since the table-extraction mechanics (`pdfplumber` lines-then-text-fallback, header detection) are county-agnostic, this task reuses `src/parsers/pdf_lines/galway_city.py`'s `extract_planning_table` core logic via a thin wrapper rather than duplicating it, differing only in `column_map` and the lack of a `_BOILERPLATE_FRAGMENTS` list tuned to County's specific PDFs (left empty, to be filled in once real samples are confirmed).

- [ ] **Step 1: Write the failing test reusing the shared extraction core with a County column map**

```python
# tests/unit/parsers/test_galway_county_pdf_lines.py
from src.parsers.pdf_lines.galway_county import extract_from_rows

COUNTY_COLUMN_MAP = {
    "file number": "file_number",
    "applicants name": "applicant",
    "app. type": "app_type",
    "date received": "date_received",
    "development description and location": "description",
}


def test_extract_from_rows_maps_county_columns():
    raw_rows = [
        ["File Number", "Applicants Name", "App. Type", "Date Received",
         "Development Description and Location"],
        ["26/9999", "Mary Byrne", "P", "03/03/2026",
         "New dwelling at Oranmore Co. Galway"],
    ]
    records = extract_from_rows(raw_rows, COUNTY_COLUMN_MAP)
    assert len(records) == 1
    assert records[0]["file_number"] == "26/9999"
    assert records[0]["applicant"] == "Mary Byrne"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/parsers/test_galway_county_pdf_lines.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.parsers.pdf_lines.galway_county'`

- [ ] **Step 3: Write `src/parsers/pdf_lines/galway_county.py`**

```python
"""
Galway County weekly-list PDF parser — built against the pdf_table_lines
family per dev-plan section 3.2's assumption that County's tabular
structure resembles City's. UNCONFIRMED against real County sample PDFs
as of this foundation pass — the source-onboarding subagent's first job
on County (per spec section 5.2) is to fetch real samples and verify this
assumption. If County's PDFs lack a text layer or use a different
structure, this parser gets reclassified to a different family.

County currently has no PDF-specific boilerplate fragments identified
(duffy never processed County PDFs) — _BOILERPLATE_FRAGMENTS is empty
pending real samples. Flag this to a human reviewer per spec section 6
step 6.
"""

from pathlib import Path

from src.parsers.pdf_lines.galway_city import (
    _extract_rows,
    _looks_like_header,
    _map_column,
    _SETTINGS_LINES,
    _SETTINGS_TEXT,
)

_BOILERPLATE_FRAGMENTS: list[str] = []  # TODO: populate once real County PDFs are reviewed


def extract_planning_table(pdf_path: Path, column_map: dict) -> list[dict]:
    import pdfplumber

    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_rows = _extract_rows(pdf, _SETTINGS_LINES)
            if not all_rows:
                all_rows = _extract_rows(pdf, _SETTINGS_TEXT)
    except Exception:
        return []

    if not all_rows:
        return []
    return extract_from_rows(all_rows, column_map)


def extract_from_rows(raw_rows: list[list], column_map: dict) -> list[dict]:
    if not raw_rows:
        return []

    header_idx = None
    for i, row in enumerate(raw_rows):
        if _looks_like_header(row):
            header_idx = i
            break
    if header_idx is None:
        return []

    raw_header = raw_rows[header_idx]
    mapped_keys = [_map_column(h, column_map) for h in raw_header]

    records: list[dict] = []
    for row in raw_rows[header_idx + 1:]:
        if all(c == "" for c in row):
            continue
        row = (row + [""] * len(mapped_keys))[: len(mapped_keys)]
        record = {k: v for k, v in zip(mapped_keys, row)}
        if record.get("file_number") or record.get("description"):
            if any(frag in str(record.get(f, "")).lower() for f in
                   ("file_number", "applicant", "description")
                   for frag in _BOILERPLATE_FRAGMENTS):
                continue
            records.append(record)
    return records
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/parsers/test_galway_county_pdf_lines.py -v`
Expected: PASS (1 test)

- [ ] **Step 5: Write the failing test for County normalization**

```python
# tests/unit/pipelines/test_normalize_galway_county.py
from src.core.normalization.galway_county import normalize_county_row

REGION_CONFIG = {
    "source_entity": "GALWAY_COUNTY_COUNCIL",
    "planning_authority": "Galway County Council",
}


def test_normalize_county_row_received():
    raw_row = {
        "file_number": "26/9999",
        "applicant": "Mary Byrne",
        "app_type": "P",
        "date_received": "03/03/2026",
        "description": "New dwelling at Oranmore Co. Galway",
    }
    app = normalize_county_row(raw_row, source_type="received", region_config=REGION_CONFIG,
                               source_file="weekly-2026-03-02-received.pdf")
    assert app.application_ref == "26/9999"
    assert app.planning_authority == "Galway County Council"
    assert app.planning_status_current == "Received"
    assert app.site_county == "Galway"
```

- [ ] **Step 6: Run test to verify it fails**

Run: `pytest tests/unit/pipelines/test_normalize_galway_county.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.core.normalization.galway_county'`

- [ ] **Step 7: Write `src/core/normalization/galway_county.py`**

```python
"""
County normalization reuses City's status/event mapping and date parsing
(both authority-agnostic) but skips Galway City's neighbourhood gazetteer
in src/core/normalization/location.py, since County addresses reference
towns (Oranmore, Tuam, ...) rather than City neighbourhoods. site_locality
extraction for County is left as a plain pass-through of the description
for this foundation pass — refining it is in scope for a future
parser-dev iteration once real address patterns are reviewed.
"""

from src.pipelines.normalize import _SOURCE_TYPE_TO_STATUS, _expand_app_type, _flag_yes, _parse_date
from src.core.schemas.application import ApplicationCreate, OtherRegulatoryFlags


def normalize_county_row(raw_row: dict, source_type: str, region_config: dict,
                         source_file: str) -> ApplicationCreate:
    status, event_type = _SOURCE_TYPE_TO_STATUS.get(source_type, ("Received", "APPLICATION_RECEIVED"))
    description = raw_row.get("description", "")
    date_received = _parse_date(raw_row.get("date_received")) or _parse_date(None)

    from datetime import datetime
    date_received = date_received or datetime.now().date()

    return ApplicationCreate(
        planning_authority=region_config["planning_authority"],
        source_entity=region_config["source_entity"],
        application_ref=raw_row.get("file_number", ""),
        applicant_name=raw_row.get("applicant", ""),
        site_address=description,
        site_locality=None,
        site_county="Galway",
        development_description=description,
        application_type=_expand_app_type(raw_row.get("app_type", "")),
        planning_status_current=status,
        status_event_type=event_type,
        date_received=date_received,
        protected_structure_flag=_flag_yes(raw_row.get("protected_structure", "")),
        eia_eis_flag=_flag_yes(raw_row.get("eis", "")),
        other_regulatory_flags=OtherRegulatoryFlags(),
        source_system="Galway County Weekly Lists PDF",
        source_file=source_file,
        raw_payload_json=raw_row,
    )
```

- [ ] **Step 8: Run test to verify it passes**

Run: `pytest tests/unit/pipelines/test_normalize_galway_county.py -v`
Expected: PASS (1 test)

- [ ] **Step 9: Commit**

```bash
git add src/parsers/pdf_lines/galway_county.py src/core/normalization/galway_county.py tests/unit/parsers/test_galway_county_pdf_lines.py tests/unit/pipelines/test_normalize_galway_county.py
git commit -m "feat: build Galway County pdf_table_lines parser and normalization from scratch"
```

---

## Task 11: `/onboard-council` Skill + `source-onboarding` and `parser-dev` Subagents

**Files:**
- Create: `.claude/agents/source-onboarding.md`
- Create: `.claude/agents/parser-dev.md`
- Create: `.claude/skills/onboard-council/SKILL.md`
- Test: `tests/unit/skills/test_onboard_council_skill_files.py`

**Interfaces:**
- Consumes: `BaseSource` ABC shape (Task 4, `src/sources/base/source.py`), `config/<county>/<region>.yaml` shape (Task 4/Task 9 — `source_entity`, `planning_authority`, `parser_family`, `pdf_patterns`), parser family directory names (`src/parsers/{pdf_lines,pdf_text_fallback,docx_state_machine,pdf_ocr}/`, Task 1).
- Produces: nothing consumed by later tasks — this is the last functional piece of the foundation. Future `/onboard-council <county> <region>` invocations (out of scope for this plan) will read these three files.

This is markdown-only — no Python to unit-test in the traditional sense. The "test" is a structural assertion that the three files exist and contain their required sections, so a reviewer has an automated check rather than only eyeballing prose. Per spec sections 6 and 7.

- [ ] **Step 1: Write the failing structural test**

```python
# tests/unit/skills/test_onboard_council_skill_files.py
from pathlib import Path

SKILL_PATH = Path(".claude/skills/onboard-council/SKILL.md")
SOURCE_AGENT_PATH = Path(".claude/agents/source-onboarding.md")
PARSER_AGENT_PATH = Path(".claude/agents/parser-dev.md")


def test_skill_file_exists_and_references_both_subagents():
    text = SKILL_PATH.read_text()
    assert "source-onboarding" in text
    assert "parser-dev" in text
    assert "docs/source-inventory.md" in text


def test_source_onboarding_agent_has_frontmatter():
    text = SOURCE_AGENT_PATH.read_text()
    assert text.startswith("---")
    assert "name: source-onboarding" in text
    assert "tools:" in text


def test_parser_dev_agent_has_frontmatter():
    text = PARSER_AGENT_PATH.read_text()
    assert text.startswith("---")
    assert "name: parser-dev" in text
    assert "tools:" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/skills/test_onboard_council_skill_files.py -v`
Expected: FAIL with `FileNotFoundError` (none of the three files exist yet)

- [ ] **Step 3: Write `.claude/agents/source-onboarding.md`**

```markdown
---
name: source-onboarding
description: Researches a council's official planning data sources — weekly-list pages, ePlanning portals, open-data/GIS layers — and downloads representative sample files. Use when onboarding a new council/region via /onboard-council, after confirming config/<county>/<region>.yaml does not already exist.
tools: WebFetch, WebSearch, Bash, Read, Write
---

You are the source-onboarding subagent for the planning-intelligence platform.
You research exactly one council/region per invocation. You do not write
parser code and you do not touch the database — that is parser-dev's job.

## Input

You will be given a county slug and region slug (e.g. `cork`, `city`), plus
the council's name if known.

## Job

1. Find the council's official planning-application data source(s). Look for,
   in priority order:
   - A weekly/periodic published list (PDF, DOCX, or HTML table) of planning
     applications received/granted/refused.
   - An ePlanning or similar searchable portal with a stable query/listing
     endpoint (look for `SearchListing`, `/api/`, or paginated JSON/XML).
   - Open-data or ArcGIS layers for historical/geospatial backfill.
2. For each source found, determine:
   - The exact URL(s).
   - File format: PDF with a text layer (try extracting text — if you get
     real characters back, it has a text layer), PDF without a text layer
     (scanned/image-only — would need OCR), DOCX, or API+JSON.
   - Update cadence (weekly, daily, monthly — check publish dates of the
     last 2-3 available lists if visible).
3. Download 1-2 representative sample files into
   `data/<county>/<region>/temp/samples/` (create the directory if needed).
   Do not download more than 2 — these are for parser-dev's development and
   testing, not a full archive.
4. Append a structured entry to `docs/source-inventory.md` (create the file
   with a header row if it doesn't exist yet) with columns: Council | Region
   | Source URL | Format | Cadence | Notes. Use real values — if cadence is
   uncertain, write your best estimate and say so in Notes rather than
   guessing silently.

## Output

Report back to the caller:
- The source(s) found, with URLs.
- The file format determination and your confidence in it.
- The local path(s) of the sample files you downloaded.
- The exact line(s) you appended to `docs/source-inventory.md`.

## Constraints

- Do not write any code under `src/`.
- Do not write or modify `config/<county>/<region>.yaml` — that is the
  calling skill's job, using your findings.
- Do not connect to or modify the database.
- If you cannot find a usable public data source after reasonable searching,
  say so explicitly rather than fabricating a plausible-looking URL.
```

- [ ] **Step 4: Write `.claude/agents/parser-dev.md`**

```markdown
---
name: parser-dev
description: Implements or adjusts a parser module for a given parser family against sample planning-application files, iterating until rows validate against the canonical schema. Use when onboarding a new council/region via /onboard-council, after source-onboarding has produced sample files and a parser family has been classified.
tools: Read, Write, Edit, Bash
---

You are the parser-dev subagent for the planning-intelligence platform.
You build exactly one parser module per invocation, against sample files
that already exist locally. You do not do source discovery or scraping —
that is source-onboarding's job, and it has already run before you start.

## Input

You will be given:
- One or more sample file paths under `data/<county>/<region>/temp/samples/`.
- A target parser family: one of `pdf_table_lines`, `pdf_table_text_fallback`,
  `docx_state_machine`, `pdf_ocr_pipeline`.
- The county/region slug the parser is for.

## Job

1. Look at an existing parser in the same family for the shape of the
   interface to match — e.g. `src/parsers/pdf_lines/galway_city.py` or
   `src/parsers/pdf_lines/galway_county.py` for `pdf_table_lines`. Every
   parser in a family exposes the same signature:
   `extract_planning_table(pdf_path: Path, column_map: dict) -> list[dict]`
   (substitute `pdf_path` for the appropriate input type per family, e.g.
   `docx_path` for `docx_state_machine`).
2. Inspect the actual sample file(s) — read the raw text/table structure
   before writing any extraction code. Do not assume the column layout
   matches an existing council; confirm it from the real file.
3. Implement `src/parsers/<family>/<county>_<region>.py` with the
   family's standard `extract_planning_table` signature.
4. Write a unit test in `tests/unit/parsers/test_<county>_<region>_<family>.py`
   that runs the parser against the real sample file (not a synthetic
   fixture) and asserts the output rows are non-empty and each row's keys
   match the column_map's target field names.
5. Run the test. Iterate on the parser until it passes against the real
   sample file — do not weaken the test to make a broken parser pass.
6. If a Pydantic validation step is in scope for this invocation (it may not
   be — check what you were asked), validate at least one extracted row
   against `src.core.schemas.application.ApplicationCreate` and report any
   field mapping that fails or is ambiguous.

## Output

Report back to the caller:
- The parser file path and its test file path.
- Test status (pass/fail) and, if passing, how many rows the sample file(s)
  produced.
- Any column/field mapping that was ambiguous or required a judgment call —
  flag these explicitly as needing human review, per the calling skill's
  step 6.

## Constraints

- Do not fetch new sample files or do any HTTP/web requests — source-onboarding
  already provided what you need. If the samples are insufficient (e.g. only
  one row, or a format source-onboarding's notes didn't anticipate), say so
  rather than inventing rows.
- Do not modify `config/<county>/<region>.yaml`.
- Do not write to the database or run the full ingestion pipeline end-to-end.
```

- [ ] **Step 5: Write `.claude/skills/onboard-council/SKILL.md`**

```markdown
---
name: onboard-council
description: Onboards a new council/region into the planning-intelligence platform — research, parser classification, scaffolding, and a working parser draft for human review. Invoke as /onboard-council <county_slug> <region_slug>, e.g. /onboard-council cork city.
---

# Onboard Council

Scaffolds source acquisition and parsing for one new council/region. Galway
City and County were built directly during the platform's foundation pass,
not through this skill — this skill is for every council added afterward.

This skill does **not** run the ingestion pipeline end-to-end and does
**not** write to the database. It only scaffolds code and config for human
review per step 6 below.

## Steps

1. **Check for existing config.** Look for `config/<county_slug>/<region_slug>.yaml`.
   If it already exists, treat this invocation as an update/resume: read the
   existing file and skip straight to step 5 with the parser family it
   already records, unless the user asked specifically to re-research the
   source.

2. **Dispatch `source-onboarding`.** Give it the county/region slug and any
   council name context available. It researches the region's planning-list
   site(s), determines file format and update cadence, downloads 1-2 sample
   files into `data/<county_slug>/<region_slug>/temp/samples/`, and appends
   findings to `docs/source-inventory.md`.

3. **Classify the parser family** from the subagent's findings:
   - `pdf_table_lines` — PDF with a text layer, tabular/columnar rows (the
     family both Galway City and Galway County use).
   - `pdf_table_text_fallback` — PDF with a text layer but inconsistent
     table structure, needing line-by-line heuristics instead of fixed
     columns.
   - `docx_state_machine` — Word documents, needs a stateful line-by-line
     parser.
   - `pdf_ocr_pipeline` — PDF with no text layer (scanned/image-only),
     needs OCR before any text extraction.

4. **Scaffold config and source module.**
   - Create `config/<county_slug>/<region_slug>.yaml` following the shape
     used by `config/galway/city.yaml` and `config/galway/county.yaml`:
     `source_entity`, `planning_authority`, `parser_family`, source URL(s),
     and `pdf_patterns` (or the equivalent filename/identification patterns
     for the chosen format).
   - Create `src/sources/<county_slug>/<region_slug>/` with a thin module
     implementing `src.sources.base.source.BaseSource` (`discover() ->
     list[dict]`, `acquire(items: list[dict]) -> list[Path]`), following the
     pattern in `src/sources/galway/city/scraper.py` or
     `src/sources/galway/county/scraper.py`.

5. **Dispatch `parser-dev`** with the sample file paths and the chosen
   parser family. It builds or adjusts
   `src/parsers/<family>/<county_slug>_<region_slug>.py` and a unit test
   under `tests/unit/parsers/`, iterating until the test passes against the
   real sample file(s).

6. **Report back to the human**, covering:
   - What was scaffolded (config path, source module path, parser path).
   - Parser test status (pass/fail, row count from sample file).
   - What needs human review before this goes further — e.g. ambiguous
     column mappings parser-dev flagged, market-derivation rules for the
     new region (does it belong to an existing market entity or need a new
     one in `src/markets/registry.py`?), and whether the source-onboarding
     subagent's cadence/format determination should be spot-checked against
     the live site.
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/unit/skills/test_onboard_council_skill_files.py -v`
Expected: PASS (3 tests)

- [ ] **Step 7: Commit**

```bash
git add .claude/agents/source-onboarding.md .claude/agents/parser-dev.md .claude/skills/onboard-council/SKILL.md tests/unit/skills/test_onboard_council_skill_files.py
git commit -m "feat: add /onboard-council skill and source-onboarding/parser-dev subagents"
```

---

## Task 12: GitHub Hosting

**Files:**
- Modify: `.gitignore` (verify all entries from Task 1 are present; add any missed during Tasks 2-11)
- Modify: `README.md` (verify collaborator/branch-protection manual steps from spec section 9 are documented — should already be present from Task 1, Step 12)
- No test file — this task is infrastructure setup, verified by manual inspection of the pushed repo, not pytest.

**Interfaces:**
- Consumes: every file created in Tasks 1-11 (this task pushes the complete foundation).
- Produces: nothing — this is the last task in the plan.

Per spec section 8: branch protection and collaborator addition are explicitly **manual, owner-only steps** (spec section 9) and must NOT be automated here — this task only creates the repo and pushes the scaffold.

- [ ] **Step 1: Verify `.gitignore` covers everything required by spec section 8**

```bash
cat .gitignore
```

Expected to see (add any that are missing from Task 1's version):
```
.venv/
__pycache__/
*.pyc
.env
data/*/*/temp/
postgres-data/
.DS_Store
*.egg-info/
```

If `postgres-data/` (the `docker-compose.yml` Postgres volume mount from
Task 1) is missing, add it:

```bash
echo "postgres-data/" >> .gitignore
```

- [ ] **Step 2: Confirm no secrets are staged**

```bash
git status
git diff --cached --name-only | grep -E '\.env$' && echo "WARNING: .env is staged — stop and unstage it" || echo "OK: no .env staged"
```

Expected: "OK: no .env staged" (only `.env.example` should ever be tracked).

- [ ] **Step 3: Stage and commit anything still uncommitted**

```bash
git add -A
git status
```

Review the output — everything listed should be expected project files
(no stray local artifacts). Then:

```bash
git commit -m "chore: finalize foundation scaffold for initial push" --allow-empty
```

(`--allow-empty` is safe here since every prior task already committed its
own changes — this step exists only to catch anything left uncommitted.)

- [ ] **Step 4: Create the GitHub repository**

```bash
gh repo create planning-intelligence --private --source=. --remote=origin
```

Expected: repo created on GitHub, `origin` remote added pointing to it.

- [ ] **Step 5: Push the scaffold to `main`**

```bash
git push -u origin main
```

Expected: push succeeds, `main` now tracks `origin/main`.

- [ ] **Step 6: Verify the push**

```bash
gh repo view planning-intelligence --web
```

Confirms the repo is visible on GitHub with the expected file tree. (Opens
in browser — if running headless, use `gh repo view planning-intelligence`
instead and check the printed file list/description.)

- [ ] **Step 7: Confirm manual-step documentation is in place**

```bash
grep -A5 "## Collaborators" README.md
grep -A8 "### Branch protection" README.md
```

Expected: both sections print real `gh` commands (collaborator add,
branch protection PUT) matching spec section 9 — these stay manual/owner-run,
never invoked by this plan or by any automation.

No commit needed for this step — it's a verification read, not a change.

- [ ] **Step 8: Add the team collaborator (manual, owner-run)**

This is the one spec-§9 "manual, owner-only" step that has a concrete
target for this project: the second team member is
[tej-juwekar](https://github.com/tej-juwekar). Run this yourself — it is
intentionally not something this plan automates or that an agent should
run unattended:

```bash
gh repo add-collaborator planning-intelligence tej-juwekar --permission push
```

Or via the web UI: `https://github.com/<your-username>/planning-intelligence/settings/access`
→ "Add people" → `tej-juwekar`.

Expected: `tej-juwekar` receives a GitHub invite to the repo with push
access. Once accepted, they can clone and follow the README's Setup and
Team workflow sections (Task 1, Step 12) — including running
`git config core.hooksPath .githooks` once so the graphify pre-commit hook
(Task 1, Step 11) is active on their machine too.

Branch protection (the README's "Branch protection" section) stays
optional and is left to your judgment — with only two contributors, a
required-PR-review rule is reasonable once both of you are pushing
regularly, but isn't required to start collaborating.

No commit needed — this step only runs `gh` commands against GitHub, not
local file changes.

---

## Self-Review

**1. Spec coverage** (against `docs/superpowers/specs/2026-06-26-foundation-design.md`):

| Spec section | Covered by |
|---|---|
| §2 Tech Stack (Python, Postgres+PostGIS, SQLAlchemy/Pydantic, pdfplumber, Alembic, fixtures) | Task 1 (`pyproject.toml`, `docker-compose.yml`), Task 2 (models/schemas), Task 3 (migrations) |
| §2.1 Python Environment (Conda/venv, README docs both) | Task 1, Step 12 (README) |
| §3 Repo Layout (full tree, `.claude/`, county grouping) | Task 1, Step 1 (directory tree) |
| §3 `markets/galway/metro.py` stub with TODO comment | Task 8, Step 9 |
| §3 `src/monitoring/metrics.py` minimal counters | Task 8, Steps 1-4 |
| §3.1 `temp/` disposable raw storage, `.gitignore`d | Task 1, Steps 1 and 5 (`.gitignore`); Task 12, Step 1 (verification) |
| §4 Canonical schema (`Application`, `ApplicationEvent`, natural key, Pydantic mirrors) | Task 2 (models + schemas), Task 3 (migration with `UniqueConstraint`) |
| §5.1 Galway City port (scraper, parser, normalize, db, config/discover) | Task 4 (config/discover), Task 5 (scraper), Task 6 (parser), Task 7 (normalize/resolve/publish) |
| §5.1 chat/RAG files explicitly NOT ported | Global Constraints section; no task references `chat_app.py`/`rag_engine.py`/etc. |
| §5.2 Galway County built fresh (HTML scraper, `pdf_table_lines` assumption flagged for confirmation, config) | Task 9 (scraper/config), Task 10 (parser/normalization) |
| §6 `/onboard-council` skill, 6-step workflow | Task 11, Step 5 (`SKILL.md`) |
| §7 `source-onboarding` and `parser-dev` subagents | Task 11, Steps 3-4 |
| §8 GitHub hosting (repo create, `.gitignore`, push) | Task 12, Steps 1-6 |
| §9 Manual collaborator/branch-protection steps (never automated) | Task 1, Step 12 (README documents the manual `gh`/web-UI steps); Task 12, Step 7 (verifies docs exist); Task 12, Step 8 (owner manually runs the actual `gh repo add-collaborator` for `tej-juwekar`) |
| §10 Deferred items (RAG, other councils, metro polygons, CI/CD) | Global Constraints section explicitly lists these as out of scope; no task implements any of them |

No gaps found — every numbered spec section maps to at least one task.

**Addendum (post-spec, user-requested):** project-level `graphify` support
was added beyond the original spec, per a direct user request that the
codebase be navigable for collaborators via `/graphify`. Covered by Task 1,
Steps 10 (`CLAUDE.md`), 11 (README "Knowledge graph" section), and 13
(generates and commits `graphify-out/`, with a note to re-run `graphify
update .` and commit at the end of each later task). `.gitignore` (Step 5)
explicitly does not exclude `graphify-out/`, with a comment explaining why —
the user confirmed they want the graph committed, not gitignored, so it's
available to every collaborator on clone without extra setup.

**2. Placeholder scan:** Searched for "TBD", "implement later", "fill in details", "add appropriate error handling", "similar to Task N" patterns across all 12 tasks. None found except the two *intentional* spec-mandated placeholders, both flagged as such in their own task text rather than left silent:
- `src/markets/galway/metro.py` (Task 8, Step 9) — spec §3/§10 explicitly require this to be a stub with a TODO comment, not a working implementation. This is a spec requirement, not a plan gap.
- County's weekly-list/ePlanning URLs in `config/galway/county.yaml` (Task 9) — spec §5.2 explicitly assigns *confirming* these to the `source-onboarding` subagent's first real job on County; the task text flags this explicitly in Task 9/10's interface notes rather than silently shipping an unverified URL as fact.

**3. Type/signature consistency check:**
- `BaseSource.discover() -> list[dict]` / `acquire(items: list[dict]) -> list[Path]` (Task 4) is implemented identically by `GalwayCityScraper` (Task 5) and `GalwayCountyScraper` (Task 9) — confirmed matching signatures.
- `extract_planning_table(pdf_path: Path, column_map: dict) -> list[dict]` (Task 6, City) is reused with the same name and signature by Task 10's County parser — confirmed, and Task 11's `parser-dev` agent definition explicitly documents this as the family-wide contract.
- `normalize_row` (Task 7, City) and `normalize_county_row` (Task 10, County) are deliberately distinct functions, not a naming inconsistency — County reuses City's private helpers (`_flag_yes`, `_expand_app_type`, `_parse_date`, `_SOURCE_TYPE_TO_STATUS`) but skips City's neighbourhood-gazetteer step (`extract_location`), which only makes sense for City's address format. Documented inline in Task 10, Step 7's docstring.
- `record_ingestion_run(region: str, rows_ingested: int, parse_errors: int) -> None` and `get_metrics_snapshot(region: str) -> dict[str, int]` (Task 8) match their usage in Task 7 Step 10's `publish.py`.
- `derive_market_entities(application) -> list[str]` (Task 8) is correctly noted as *not* wired into the publish pipeline yet (metro polygons deferred per spec §10) — consistent with Global Constraints.
- Four stale `Task 13` cross-references (in Tasks 2, 3, 5, 7's Interfaces blocks) were found pointing at a task number that doesn't exist in the final plan — these have been corrected to point at Task 11 (`/onboard-council` skill) or reworded to "future onboarded regions" where no specific task applies.

No further issues found.

---
