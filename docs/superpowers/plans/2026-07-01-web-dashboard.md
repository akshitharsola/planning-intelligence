# Web Dashboard v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal local FastAPI + Jinja2 dashboard showing real
Galway planning-application data with a filterable/paginated table, 3
charts, KPI cards, and a per-application detail page with full provenance.

**Architecture:** Two plain-function service modules
(`src/services/dashboard_service.py`, `src/services/application_service.py`)
query the existing `Application` model via SQLAlchemy. A new
`src/web/main.py` FastAPI app wires two routes (`/` and
`/applications/{planning_authority}/{application_ref}`) to those services
and renders Jinja2 templates. Charts render via Chart.js from a CDN, fed by
JSON inlined in the dashboard template. No new abstraction layers, no
changes to ingestion code.

**Tech Stack:** FastAPI, Uvicorn, Jinja2, existing SQLAlchemy/Postgres
stack, Chart.js (CDN), pytest (existing).

## Global Constraints

- Reuse `src.core.db.session.SessionLocal` unchanged — do not modify it.
- Field names are snake_case exactly as in `src/core/models/application.py`
  — no renaming anywhere (queries, templates, routes, tests).
- No React/Vue/Next.js/build tooling. Server-rendered HTML only, one CSS
  file, one JS file (charts only).
- No new ORM abstraction layer — service functions take a `Session` and
  return dicts/lists/ORM rows directly.
- No maps/geometry, auth, RAG, background jobs, cloud deploy, or ingestion
  logic changes.
- New deps limited to: `fastapi`, `uvicorn[standard]`, `jinja2`.
- Filter query params: `planning_authority`, `planning_status_current`,
  `application_type`, `date_received_from`, `date_received_to`, `q`, `page`,
  `page_size`.
- `q` matches case-insensitively (ILIKE) across `applicant_name`,
  `site_address`, `development_description`.
- Tests run against the real local dev Postgres DB (existing project
  convention — see `tests/integration/test_ingest_galway_city.py`), using a
  distinctive test-only `application_ref` prefix and explicit
  `DELETE ... LIKE 'PREFIX/%'` cleanup in a `_cleanup()` helper, not a
  separate test DB or mocking framework.
- **Table ordering:** the applications table (both dashboard route and
  `search()`) always orders by `date_received DESC` as its sole sort key,
  for deterministic pagination. This is fixed for v1 — no user-selectable
  sort column.
- **Charts are global, not filter-aware:** `get_monthly_counts`,
  `get_status_breakdown`, and `get_type_breakdown` always aggregate over
  the *entire* `applications` table, independent of whatever filters are
  applied to the table below them. Only the table and its pagination/total
  count respond to filters. This keeps v1 simple (one cheap set of chart
  queries per page load) and avoids the ambiguity of what a "filtered
  chart" should mean when, e.g., a status filter is applied to a status
  breakdown chart. If filter-aware charts are wanted later, that's a v2
  follow-up, not part of this plan.
- **Filter inputs are plain text fields in v1**, not dropdowns/selects.
  Verified live-data values for reference (queried from the real dev DB on
  2026-07-01): `planning_status_current` is one of `Received`, `Granted`,
  `Refused`, `Withdrawn`, `Invalid` (note: title case, not upper case);
  `application_type` values are inconsistent free-text strings from source
  data (e.g. `Permission`, `OUTLINE PERMISSION`, `RETENTION`,
  `EXTENSION OF DURATION`, `PERMISSION CONSEQUENT`); `planning_authority` is
  one of `Galway City Council`, `Galway County Council`. Text inputs avoid
  hardcoding these lists into the UI (they may grow as new councils are
  onboarded) — converting to dropdowns populated from
  `SELECT DISTINCT ...` is a reasonable v2 improvement but out of scope
  here.
- **Natural-key route verified safe:** live-data check found only 1 of
  20,329 real `application_ref` values contains a `/` (`'TEST/0001'`, a
  test artifact, not production data). The
  `/applications/{planning_authority}/{application_ref:path}` route in
  Task 4 already uses the `:path` converter specifically so slash-bearing
  refs still resolve correctly — this was already correct in the original
  plan and needs no change, but is called out here explicitly since it's
  the single riskiest routing decision in the plan.

---

### Task 1: Add web dependencies

**Files:**
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: `fastapi`, `uvicorn`, `jinja2` importable in the venv for all
  later tasks.

- [ ] **Step 1: Add dependencies to `pyproject.toml`**

Edit the `dependencies` list in `pyproject.toml` to add three lines after
`"PyYAML>=6.0",`:

```toml
    "PyYAML>=6.0",
    "fastapi>=0.110",
    "uvicorn[standard]>=0.29",
    "jinja2>=3.1",
]
```

- [ ] **Step 2: Install the updated dependencies**

Run: `pip install -e .`
Expected: install completes, `fastapi`, `uvicorn`, `jinja2` present.

- [ ] **Step 3: Verify imports work**

Run: `python -c "import fastapi, uvicorn, jinja2; print('ok')"`
Expected: prints `ok`

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add fastapi, uvicorn, jinja2 for web dashboard"
```

---

### Task 2: `dashboard_service.py` — summary and chart queries

**Files:**
- Create: `src/services/dashboard_service.py`
- Test: `tests/integration/test_dashboard_service.py`

**Interfaces:**
- Consumes: `src.core.db.session.SessionLocal`, `src.core.models.application.Application`.
- Produces:
  - `get_summary(db: Session) -> dict` with keys `total_applications: int`,
    `distinct_authorities: int`, `earliest_received: date | None`,
    `latest_received: date | None`, `latest_ingested_at: datetime | None`.
  - `get_monthly_counts(db: Session) -> list[dict]`, each
    `{"label": str, "value": int}`, `label` is `YYYY-MM`, sorted ascending.
  - `get_status_breakdown(db: Session) -> list[dict]`, each
    `{"label": str, "value": int}`, `label` is `planning_status_current`,
    sorted by `value` descending.
  - `get_type_breakdown(db: Session) -> list[dict]`, each
    `{"label": str, "value": int}`, `label` is `application_type`, sorted by
    `value` descending.

- [ ] **Step 1: Write the failing tests**

Create `tests/integration/test_dashboard_service.py`:

```python
from datetime import date, datetime

from sqlalchemy import text

from src.core.db.session import SessionLocal
from src.services.dashboard_service import (
    get_summary,
    get_monthly_counts,
    get_status_breakdown,
    get_type_breakdown,
)

PREFIX = "DASHTEST"


def _cleanup():
    session = SessionLocal()
    try:
        session.execute(
            text("DELETE FROM application_events WHERE application_ref LIKE :p"),
            {"p": f"{PREFIX}/%"},
        )
        session.execute(
            text("DELETE FROM applications WHERE application_ref LIKE :p"),
            {"p": f"{PREFIX}/%"},
        )
        session.commit()
    finally:
        session.close()


def _insert_application(session, ref, authority, status, app_type, received, ingested_at):
    session.execute(
        text(
            """
            INSERT INTO applications (
                id, planning_authority, source_entity, application_ref,
                applicant_name, development_description, application_type,
                planning_status_current, date_received, source_system,
                source_file, source_ingested_at
            ) VALUES (
                gen_random_uuid(), :authority, :authority, :ref,
                'Test Applicant', 'Test development', :app_type,
                :status, :received, 'TEST', 'test.pdf', :ingested_at
            )
            """
        ),
        {
            "authority": authority,
            "ref": ref,
            "app_type": app_type,
            "status": status,
            "received": received,
            "ingested_at": ingested_at,
        },
    )


def _seed():
    session = SessionLocal()
    try:
        _insert_application(
            session, f"{PREFIX}/0001", "Galway City Council", "Granted", "Permission",
            date(2026, 1, 15), datetime(2026, 1, 16, 9, 0),
        )
        _insert_application(
            session, f"{PREFIX}/0002", "Galway City Council", "Granted", "Permission",
            date(2026, 1, 20), datetime(2026, 1, 21, 9, 0),
        )
        _insert_application(
            session, f"{PREFIX}/0003", "Galway County Council", "Refused", "RETENTION",
            date(2026, 2, 5), datetime(2026, 2, 6, 9, 0),
        )
        session.commit()
    finally:
        session.close()


def test_get_summary_counts_and_ranges():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            summary = get_summary(session)
        finally:
            session.close()
        assert summary["total_applications"] >= 3
        assert summary["distinct_authorities"] >= 2
        assert summary["earliest_received"] <= date(2026, 1, 15)
        assert summary["latest_received"] >= date(2026, 2, 5)
        assert summary["latest_ingested_at"] >= datetime(2026, 2, 6, 9, 0)
    finally:
        _cleanup()


def test_get_monthly_counts_groups_by_year_month():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            counts = get_monthly_counts(session)
        finally:
            session.close()
        by_label = {row["label"]: row["value"] for row in counts}
        assert by_label.get("2026-01", 0) >= 2
        assert by_label.get("2026-02", 0) >= 1
    finally:
        _cleanup()


def test_get_status_breakdown_groups_by_status():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            breakdown = get_status_breakdown(session)
        finally:
            session.close()
        by_label = {row["label"]: row["value"] for row in breakdown}
        assert by_label.get("Granted", 0) >= 2
        assert by_label.get("Refused", 0) >= 1
    finally:
        _cleanup()


def test_get_type_breakdown_groups_by_application_type():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            breakdown = get_type_breakdown(session)
        finally:
            session.close()
        by_label = {row["label"]: row["value"] for row in breakdown}
        assert by_label.get("Permission", 0) >= 2
        assert by_label.get("RETENTION", 0) >= 1
    finally:
        _cleanup()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/integration/test_dashboard_service.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.services.dashboard_service'`

- [ ] **Step 3: Implement `src/services/dashboard_service.py`**

```python
from datetime import date, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.core.models.application import Application


def get_summary(db: Session) -> dict:
    row = db.query(
        func.count(Application.id),
        func.count(func.distinct(Application.planning_authority)),
        func.min(Application.date_received),
        func.max(Application.date_received),
        func.max(Application.source_ingested_at),
    ).one()
    total, distinct_authorities, earliest, latest, latest_ingested = row
    return {
        "total_applications": total,
        "distinct_authorities": distinct_authorities,
        "earliest_received": earliest,
        "latest_received": latest,
        "latest_ingested_at": latest_ingested,
    }


def get_monthly_counts(db: Session) -> list[dict]:
    month_expr = func.to_char(Application.date_received, "YYYY-MM")
    rows = (
        db.query(month_expr.label("label"), func.count(Application.id).label("value"))
        .group_by(month_expr)
        .order_by(month_expr)
        .all()
    )
    return [{"label": r.label, "value": r.value} for r in rows]


def get_status_breakdown(db: Session) -> list[dict]:
    rows = (
        db.query(
            Application.planning_status_current.label("label"),
            func.count(Application.id).label("value"),
        )
        .group_by(Application.planning_status_current)
        .order_by(func.count(Application.id).desc())
        .all()
    )
    return [{"label": r.label, "value": r.value} for r in rows]


def get_type_breakdown(db: Session) -> list[dict]:
    rows = (
        db.query(
            Application.application_type.label("label"),
            func.count(Application.id).label("value"),
        )
        .group_by(Application.application_type)
        .order_by(func.count(Application.id).desc())
        .all()
    )
    return [{"label": r.label, "value": r.value} for r in rows]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/integration/test_dashboard_service.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add src/services/dashboard_service.py tests/integration/test_dashboard_service.py
git commit -m "feat: add dashboard_service summary and chart queries"
```

---

### Task 3: `application_service.py` — search and detail lookup

**Files:**
- Create: `src/services/application_service.py`
- Test: `tests/integration/test_application_service.py`

**Interfaces:**
- Consumes: `src.core.models.application.Application`.
- Produces:
  - `search(db: Session, filters: dict, page: int, page_size: int) -> tuple[list[Application], int]`.
    `filters` keys (all optional, absent/`None` means "no filter"):
    `planning_authority`, `planning_status_current`, `application_type`,
    `date_received_from` (`date`), `date_received_to` (`date`), `q` (`str`).
    Returns `(rows, total_count)` where `rows` is the page slice and
    `total_count` is the count across all matching rows (pre-pagination).
  - `get_by_natural_key(db: Session, planning_authority: str, application_ref: str) -> Application | None`.

- [ ] **Step 1: Write the failing tests**

Create `tests/integration/test_application_service.py`:

```python
from datetime import date

from sqlalchemy import text

from src.core.db.session import SessionLocal
from src.services.application_service import search, get_by_natural_key

PREFIX = "APPSVCTEST"


def _cleanup():
    session = SessionLocal()
    try:
        session.execute(
            text("DELETE FROM application_events WHERE application_ref LIKE :p"),
            {"p": f"{PREFIX}/%"},
        )
        session.execute(
            text("DELETE FROM applications WHERE application_ref LIKE :p"),
            {"p": f"{PREFIX}/%"},
        )
        session.commit()
    finally:
        session.close()


def _insert(session, ref, authority, status, app_type, received, applicant, address, description):
    session.execute(
        text(
            """
            INSERT INTO applications (
                id, planning_authority, source_entity, application_ref,
                applicant_name, site_address, development_description,
                application_type, planning_status_current, date_received,
                source_system, source_file, source_ingested_at
            ) VALUES (
                gen_random_uuid(), :authority, :authority, :ref,
                :applicant, :address, :description, :app_type, :status,
                :received, 'TEST', 'test.pdf', now()
            )
            """
        ),
        {
            "authority": authority,
            "ref": ref,
            "applicant": applicant,
            "address": address,
            "description": description,
            "app_type": app_type,
            "status": status,
            "received": received,
        },
    )


def _seed():
    session = SessionLocal()
    try:
        _insert(
            session, f"{PREFIX}/0001", "Galway City Council", "Granted", "Permission",
            date(2026, 1, 15), "Alice Example", "1 Main Street, Galway",
            "New dwelling extension",
        )
        _insert(
            session, f"{PREFIX}/0002", "Galway County Council", "Refused", "RETENTION",
            date(2026, 2, 5), "Bob Sample", "2 Bridge Road, Oranmore",
            "Commercial signage installation",
        )
        session.commit()
    finally:
        session.close()


def test_get_by_natural_key_found():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            app = get_by_natural_key(session, "Galway City Council", f"{PREFIX}/0001")
        finally:
            session.close()
        assert app is not None
        assert app.applicant_name == "Alice Example"
    finally:
        _cleanup()


def test_get_by_natural_key_not_found_returns_none():
    session = SessionLocal()
    try:
        app = get_by_natural_key(session, "Galway City Council", "NOSUCHREF/9999")
    finally:
        session.close()
    assert app is None


def test_search_filters_by_planning_authority():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            rows, total = search(
                session,
                {"planning_authority": "Galway County Council", "q": None},
                page=1,
                page_size=25,
            )
        finally:
            session.close()
        refs = {r.application_ref for r in rows}
        assert f"{PREFIX}/0002" in refs
        assert f"{PREFIX}/0001" not in refs
        assert total == len(rows)
    finally:
        _cleanup()


def test_search_q_matches_site_address_case_insensitive():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            rows, total = search(session, {"q": "bridge road"}, page=1, page_size=25)
        finally:
            session.close()
        refs = {r.application_ref for r in rows}
        assert f"{PREFIX}/0002" in refs
        assert f"{PREFIX}/0001" not in refs
    finally:
        _cleanup()


def test_search_pagination_returns_correct_slice_and_total():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            rows_page1, total1 = search(
                session, {"q": PREFIX}, page=1, page_size=1
            )
            rows_page2, total2 = search(
                session, {"q": PREFIX}, page=2, page_size=1
            )
        finally:
            session.close()
        assert len(rows_page1) == 1
        assert len(rows_page2) == 1
        assert rows_page1[0].application_ref != rows_page2[0].application_ref
        assert total1 == total2 == 2
    finally:
        _cleanup()
```

Note: `q` in `test_search_pagination_returns_correct_slice_and_total` relies
on `q` matching `PREFIX` inside `application_ref`... but `search`'s `q` only
matches `applicant_name`/`site_address`/`development_description` per the
spec, not `application_ref`. Use a substring common to both descriptions
instead so the test is correct: both seeded descriptions do not share a
word. Fix by filtering on `planning_authority` being one of the two test
authorities isn't a single filter either. Simplest correct approach: add a
shared marker to both `development_description` values in `_seed` (e.g.
append `"(APPSVCTEST)"` to both descriptions) and filter on `q="APPSVCTEST"`.
Update `_insert` calls in `_seed` accordingly before running this test.

- [ ] **Step 2: Fix the seed data for the pagination test**

In the `_seed()` function above, change the two description arguments so
both contain the shared marker:

```python
        _insert(
            session, f"{PREFIX}/0001", "Galway City Council", "Granted", "Permission",
            date(2026, 1, 15), "Alice Example", "1 Main Street, Galway",
            "New dwelling extension (APPSVCTEST)",
        )
        _insert(
            session, f"{PREFIX}/0002", "Galway County Council", "Refused", "RETENTION",
            date(2026, 2, 5), "Bob Sample", "2 Bridge Road, Oranmore",
            "Commercial signage installation (APPSVCTEST)",
        )
```

And change the pagination test's `q` value from `PREFIX` to `"APPSVCTEST"`
(same string, already matches — no further change needed since `PREFIX ==
"APPSVCTEST"`). Confirm `PREFIX = "APPSVCTEST"` at the top of the file
already matches — it does, so no additional edit is required beyond fixing
the descriptions above.

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/integration/test_application_service.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.services.application_service'`

- [ ] **Step 4: Implement `src/services/application_service.py`**

```python
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from src.core.models.application import Application


def get_by_natural_key(db: Session, planning_authority: str, application_ref: str) -> Application | None:
    return (
        db.query(Application)
        .filter(
            Application.planning_authority == planning_authority,
            Application.application_ref == application_ref,
        )
        .one_or_none()
    )


def search(db: Session, filters: dict, page: int, page_size: int) -> tuple[list[Application], int]:
    query = db.query(Application)

    planning_authority = filters.get("planning_authority")
    if planning_authority:
        query = query.filter(Application.planning_authority == planning_authority)

    planning_status_current = filters.get("planning_status_current")
    if planning_status_current:
        query = query.filter(Application.planning_status_current == planning_status_current)

    application_type = filters.get("application_type")
    if application_type:
        query = query.filter(Application.application_type == application_type)

    date_received_from = filters.get("date_received_from")
    if date_received_from:
        query = query.filter(Application.date_received >= date_received_from)

    date_received_to = filters.get("date_received_to")
    if date_received_to:
        query = query.filter(Application.date_received <= date_received_to)

    q = filters.get("q")
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Application.applicant_name.ilike(pattern),
                Application.site_address.ilike(pattern),
                Application.development_description.ilike(pattern),
            )
        )

    total = query.with_entities(func.count(Application.id)).scalar()

    rows = (
        query.order_by(Application.date_received.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return rows, total
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/integration/test_application_service.py -v`
Expected: PASS (5 passed)

- [ ] **Step 6: Commit**

```bash
git add src/services/application_service.py tests/integration/test_application_service.py
git commit -m "feat: add application_service search and natural-key lookup"
```

---

### Task 4: FastAPI app skeleton and `get_db` dependency

**Files:**
- Create: `src/web/__init__.py`
- Create: `src/web/main.py`
- Test: `tests/integration/test_web_routes.py`

**Interfaces:**
- Consumes: `src.core.db.session.SessionLocal`,
  `src.services.dashboard_service.*`, `src.services.application_service.*`.
- Produces: FastAPI `app` object in `src.web.main`, importable as
  `from src.web.main import app`. Routes `/` and
  `/applications/{planning_authority}/{application_ref}` (bodies filled in
  Tasks 6–7; this task creates the app, `get_db`, and route stubs returning
  200/404 so smoke tests can run before templates exist).

- [ ] **Step 1: Write the failing smoke test**

Create `tests/integration/test_web_routes.py`:

```python
from fastapi.testclient import TestClient

from src.web.main import app

client = TestClient(app)


def test_dashboard_route_returns_200():
    response = client.get("/")
    assert response.status_code == 200


def test_detail_route_returns_404_for_unknown_application():
    response = client.get("/applications/Galway City Council/NOSUCHREF%2F9999")
    assert response.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_web_routes.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.web'`

- [ ] **Step 3: Create `src/web/__init__.py`**

```python
```

(empty file)

- [ ] **Step 4: Create `src/web/main.py` with app, `get_db`, and route stubs**

```python
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.core.db.session import SessionLocal
from src.services import application_service, dashboard_service

WEB_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Planning Intelligence Dashboard")
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")
templates = Jinja2Templates(directory=WEB_DIR / "templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    summary = dashboard_service.get_summary(db)
    return templates.TemplateResponse(
        request, "dashboard.html", {"summary": summary}
    )


@app.get("/applications/{planning_authority}/{application_ref:path}", response_class=HTMLResponse)
def application_detail(
    request: Request,
    planning_authority: str,
    application_ref: str,
    db: Session = Depends(get_db),
):
    application = application_service.get_by_natural_key(db, planning_authority, application_ref)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return templates.TemplateResponse(
        request, "application_detail.html", {"application": application}
    )
```

Note: `application_ref:path` is used because some application refs contain
`/` (e.g. `P/2026/0001`); this lets FastAPI capture the full ref including
slashes as one path segment. `planning_authority` values in this dataset
(e.g. `Galway City Council`) do not contain `/`, so the default path
converter is fine for it.

- [ ] **Step 5: Create placeholder templates so `TemplateResponse` doesn't 500**

Create `src/web/templates/dashboard.html`:

```html
<!DOCTYPE html>
<html>
<head><title>Planning Intelligence Dashboard</title></head>
<body>
<h1>Planning Intelligence Dashboard</h1>
<p>Total applications: {{ summary.total_applications }}</p>
</body>
</html>
```

Create `src/web/templates/application_detail.html`:

```html
<!DOCTYPE html>
<html>
<head><title>Application {{ application.application_ref }}</title></head>
<body>
<h1>{{ application.application_ref }}</h1>
<p>{{ application.planning_authority }}</p>
</body>
</html>
```

Create empty `src/web/static/app.css` and `src/web/static/app.js` (empty
files, just so `StaticFiles` has a directory to mount — content added in
Task 5).

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/integration/test_web_routes.py -v`
Expected: PASS (2 passed)

- [ ] **Step 7: Commit**

```bash
git add src/web tests/integration/test_web_routes.py
git commit -m "feat: add FastAPI app skeleton with dashboard and detail route stubs"
```

---

### Task 5: Dashboard page — KPIs, charts, filters, paginated table

**Files:**
- Modify: `src/web/main.py`
- Create: `src/web/templates/partials/application_table.html`
- Modify: `src/web/templates/dashboard.html`
- Modify: `src/web/static/app.css`
- Modify: `src/web/static/app.js`
- Test: `tests/integration/test_web_routes.py` (extend)

**Interfaces:**
- Consumes: `dashboard_service.get_summary/get_monthly_counts/get_status_breakdown/get_type_breakdown`,
  `application_service.search`.
- Produces: fully wired `/` route rendering real KPI data, 3 Chart.js
  charts, a filter form, and a paginated table partial.

- [ ] **Step 1: Write the extended failing tests**

Append to `tests/integration/test_web_routes.py`:

```python
def test_dashboard_shows_kpi_and_chart_containers():
    response = client.get("/")
    assert response.status_code == 200
    assert "Total applications" in response.text
    assert "monthly-chart" in response.text
    assert "status-chart" in response.text
    assert "type-chart" in response.text


def test_dashboard_filter_by_planning_authority_narrows_table():
    response = client.get("/", params={"planning_authority": "Galway City Council"})
    assert response.status_code == 200


def test_dashboard_pagination_params_accepted():
    response = client.get("/", params={"page": 2, "page_size": 10})
    assert response.status_code == 200
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/integration/test_web_routes.py -v`
Expected: FAIL on `test_dashboard_shows_kpi_and_chart_containers` (missing
chart container ids/text in placeholder template)

- [ ] **Step 3: Update the `/` route in `src/web/main.py`**

Replace the `dashboard` function body:

```python
from datetime import date

from fastapi import Query


@app.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    planning_authority: str | None = Query(default=None),
    planning_status_current: str | None = Query(default=None),
    application_type: str | None = Query(default=None),
    date_received_from: date | None = Query(default=None),
    date_received_to: date | None = Query(default=None),
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    summary = dashboard_service.get_summary(db)
    monthly_counts = dashboard_service.get_monthly_counts(db)
    status_breakdown = dashboard_service.get_status_breakdown(db)
    type_breakdown = dashboard_service.get_type_breakdown(db)

    filters = {
        "planning_authority": planning_authority,
        "planning_status_current": planning_status_current,
        "application_type": application_type,
        "date_received_from": date_received_from,
        "date_received_to": date_received_to,
        "q": q,
    }
    rows, total = application_service.search(db, filters, page=page, page_size=page_size)
    total_pages = max(1, (total + page_size - 1) // page_size)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "summary": summary,
            "monthly_counts": monthly_counts,
            "status_breakdown": status_breakdown,
            "type_breakdown": type_breakdown,
            "applications": rows,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "filters": filters,
        },
    )
```

Move the `from datetime import date` and `from fastapi import Query` imports
to the top of the file alongside the existing imports rather than inline.

- [ ] **Step 4: Create `src/web/templates/partials/application_table.html`**

```html
<table id="application-table">
  <thead>
    <tr>
      <th>Planning Authority</th>
      <th>Application Ref</th>
      <th>Applicant</th>
      <th>Type</th>
      <th>Status</th>
      <th>Date Received</th>
    </tr>
  </thead>
  <tbody>
    {% for app in applications %}
    <tr>
      <td>{{ app.planning_authority }}</td>
      <td>
        <a href="/applications/{{ app.planning_authority | urlencode }}/{{ app.application_ref | urlencode }}">
          {{ app.application_ref }}
        </a>
      </td>
      <td>{{ app.applicant_name }}</td>
      <td>{{ app.application_type }}</td>
      <td>{{ app.planning_status_current }}</td>
      <td>{{ app.date_received }}</td>
    </tr>
    {% else %}
    <tr><td colspan="6">No applications match the current filters.</td></tr>
    {% endfor %}
  </tbody>
</table>

<div id="pagination">
  <span>Page {{ page }} of {{ total_pages }} ({{ total }} total)</span>
  {% if page > 1 %}
  <a href="?{{ request.query_params | replace_param('page', page - 1) }}">Previous</a>
  {% endif %}
  {% if page < total_pages %}
  <a href="?{{ request.query_params | replace_param('page', page + 1) }}">Next</a>
  {% endif %}
</div>
```

Note: Jinja2 has no built-in `replace_param` filter for query strings.
Register one in `src/web/main.py` instead of relying on template magic —
add before the route definitions:

```python
from urllib.parse import urlencode


def _replace_param(query_params, key, value):
    merged = dict(query_params)
    merged[key] = value
    return urlencode(merged)


templates.env.filters["replace_param"] = _replace_param
```

- [ ] **Step 5: Replace `src/web/templates/dashboard.html`**

```html
<!DOCTYPE html>
<html>
<head>
  <title>Planning Intelligence Dashboard</title>
  <link rel="stylesheet" href="/static/app.css">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
  <h1>Planning Intelligence Dashboard</h1>

  <section id="kpi-cards">
    <div class="kpi-card">
      <span class="kpi-label">Total applications</span>
      <span class="kpi-value">{{ summary.total_applications }}</span>
    </div>
    <div class="kpi-card">
      <span class="kpi-label">Councils covered</span>
      <span class="kpi-value">{{ summary.distinct_authorities }}</span>
    </div>
    <div class="kpi-card">
      <span class="kpi-label">Coverage date range</span>
      <span class="kpi-value">{{ summary.earliest_received }} &ndash; {{ summary.latest_received }}</span>
    </div>
    <div class="kpi-card">
      <span class="kpi-label">Last ingestion</span>
      <span class="kpi-value">{{ summary.latest_ingested_at }}</span>
    </div>
  </section>

  <section id="charts">
    <canvas id="monthly-chart"></canvas>
    <canvas id="status-chart"></canvas>
    <canvas id="type-chart"></canvas>
  </section>

  <script>
    const monthlyData = {{ monthly_counts | tojson }};
    const statusData = {{ status_breakdown | tojson }};
    const typeData = {{ type_breakdown | tojson }};
  </script>
  <script src="/static/app.js"></script>

  <section id="filters">
    <form method="get" action="/">
      <input type="text" name="planning_authority" placeholder="Planning authority" value="{{ filters.planning_authority or '' }}">
      <input type="text" name="planning_status_current" placeholder="Status" value="{{ filters.planning_status_current or '' }}">
      <input type="text" name="application_type" placeholder="Application type" value="{{ filters.application_type or '' }}">
      <input type="date" name="date_received_from" value="{{ filters.date_received_from or '' }}">
      <input type="date" name="date_received_to" value="{{ filters.date_received_to or '' }}">
      <input type="text" name="q" placeholder="Search applicant, address, description" value="{{ filters.q or '' }}">
      <button type="submit">Filter</button>
    </form>
  </section>

  <section id="applications-table">
    {% include "partials/application_table.html" %}
  </section>
</body>
</html>
```

- [ ] **Step 6: Write `src/web/static/app.js`**

```javascript
function renderBarChart(canvasId, data, label) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  new Chart(ctx, {
    type: "bar",
    data: {
      labels: data.map((row) => row.label),
      datasets: [{ label, data: data.map((row) => row.value) }],
    },
  });
}

document.addEventListener("DOMContentLoaded", () => {
  renderBarChart("monthly-chart", monthlyData, "Applications received per month");
  renderBarChart("status-chart", statusData, "Applications by status");
  renderBarChart("type-chart", typeData, "Applications by type");
});
```

- [ ] **Step 7: Write `src/web/static/app.css`**

```css
body {
  font-family: system-ui, sans-serif;
  margin: 2rem;
  color: #1a1a1a;
  background: #fafafa;
}

#kpi-cards {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}

.kpi-card {
  border: 1px solid #ccc;
  padding: 1rem;
  min-width: 150px;
}

.kpi-label {
  display: block;
  font-size: 0.85rem;
  color: #555;
}

.kpi-value {
  display: block;
  font-size: 1.4rem;
  font-weight: 600;
}

#charts {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}

#charts canvas {
  max-height: 250px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  border-bottom: 1px solid #ddd;
  padding: 0.5rem;
  text-align: left;
}
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `pytest tests/integration/test_web_routes.py -v`
Expected: PASS (5 passed)

- [ ] **Step 9: Manually verify in a browser**

Run: `uvicorn src.web.main:app --reload` then open `http://localhost:8000`
in a browser. Confirm KPI cards show real numbers, 3 charts render, the
filter form is visible, and the table lists rows with working detail links.

- [ ] **Step 10: Commit**

```bash
git add src/web tests/integration/test_web_routes.py
git commit -m "feat: wire dashboard KPIs, charts, filters, and paginated table"
```

---

### Task 6: Application detail page with full provenance

**Files:**
- Modify: `src/web/templates/application_detail.html`
- Test: `tests/integration/test_web_routes.py` (extend)

**Interfaces:**
- Consumes: `application_service.get_by_natural_key` (already wired in
  Task 4).
- Produces: fully rendered detail page showing all fields listed in the
  spec.

- [ ] **Step 1: Seed a known test row and write the failing test**

Append to `tests/integration/test_web_routes.py`:

```python
from datetime import date

from sqlalchemy import text

from src.core.db.session import SessionLocal

DETAIL_PREFIX = "WEBDETAILTEST"


def _cleanup_detail():
    session = SessionLocal()
    try:
        session.execute(
            text("DELETE FROM applications WHERE application_ref LIKE :p"),
            {"p": f"{DETAIL_PREFIX}/%"},
        )
        session.commit()
    finally:
        session.close()


def _seed_detail():
    session = SessionLocal()
    try:
        session.execute(
            text(
                """
                INSERT INTO applications (
                    id, planning_authority, source_entity, application_ref,
                    applicant_name, site_address, site_locality, site_county,
                    development_description, application_type,
                    planning_status_current, date_received, decision_due_date,
                    decision_date, further_information_flag,
                    protected_structure_flag, eia_eis_flag, official_detail_url,
                    official_documents_url, source_system, source_file,
                    source_ingested_at
                ) VALUES (
                    gen_random_uuid(), 'Galway City Council', 'GALWAY_CITY_COUNCIL',
                    :ref, 'Carol Example', '5 Test Lane', 'Galway City', 'Galway',
                    'Test detail page development', 'Permission', 'Granted',
                    :received, :due, :decided, true, false, false,
                    'https://example.test/detail', 'https://example.test/docs',
                    'TEST', 'test.pdf', now()
                )
                """
            ),
            {
                "ref": f"{DETAIL_PREFIX}/0001",
                "received": date(2026, 1, 10),
                "due": date(2026, 3, 10),
                "decided": date(2026, 3, 1),
            },
        )
        session.commit()
    finally:
        session.close()


def test_detail_page_shows_all_expected_fields():
    _cleanup_detail()
    _seed_detail()
    try:
        response = client.get(f"/applications/Galway City Council/{DETAIL_PREFIX}%2F0001")
        assert response.status_code == 200
        body = response.text
        for expected in [
            "Galway City Council", f"{DETAIL_PREFIX}/0001", "Carol Example",
            "5 Test Lane", "Galway City", "Test detail page development",
            "Granted", "2026-01-10", "2026-03-10", "2026-03-01",
            "TEST", "test.pdf", "https://example.test/detail",
            "https://example.test/docs",
        ]:
            assert expected in body
    finally:
        _cleanup_detail()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_web_routes.py::test_detail_page_shows_all_expected_fields -v`
Expected: FAIL (placeholder template doesn't show most fields)

- [ ] **Step 3: Replace `src/web/templates/application_detail.html`**

```html
<!DOCTYPE html>
<html>
<head>
  <title>{{ application.application_ref }}</title>
  <link rel="stylesheet" href="/static/app.css">
</head>
<body>
  <a href="/">&larr; Back to dashboard</a>
  <h1>{{ application.application_ref }}</h1>
  <p>{{ application.planning_authority }}</p>

  <table>
    <tr><th>Applicant</th><td>{{ application.applicant_name }}</td></tr>
    <tr><th>Site address</th><td>{{ application.site_address }}</td></tr>
    <tr><th>Site locality</th><td>{{ application.site_locality }}</td></tr>
    <tr><th>Site county</th><td>{{ application.site_county }}</td></tr>
    <tr><th>Description</th><td>{{ application.development_description }}</td></tr>
    <tr><th>Application type</th><td>{{ application.application_type }}</td></tr>
    <tr><th>Current status</th><td>{{ application.planning_status_current }}</td></tr>
    <tr><th>Date received</th><td>{{ application.date_received }}</td></tr>
    <tr><th>Decision due date</th><td>{{ application.decision_due_date }}</td></tr>
    <tr><th>Decision date</th><td>{{ application.decision_date }}</td></tr>
    <tr><th>Further information requested</th><td>{{ application.further_information_flag }}</td></tr>
    <tr><th>Protected structure</th><td>{{ application.protected_structure_flag }}</td></tr>
    <tr><th>EIA/EIS</th><td>{{ application.eia_eis_flag }}</td></tr>
  </table>

  <h2>Provenance</h2>
  <table>
    <tr><th>Source system</th><td>{{ application.source_system }}</td></tr>
    <tr><th>Source file</th><td>{{ application.source_file }}</td></tr>
    <tr><th>Source ingested at</th><td>{{ application.source_ingested_at }}</td></tr>
    {% if application.official_detail_url %}
    <tr><th>Official detail URL</th><td><a href="{{ application.official_detail_url }}">{{ application.official_detail_url }}</a></td></tr>
    {% endif %}
    {% if application.official_documents_url %}
    <tr><th>Official documents URL</th><td><a href="{{ application.official_documents_url }}">{{ application.official_documents_url }}</a></td></tr>
    {% endif %}
  </table>
</body>
</html>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_web_routes.py::test_detail_page_shows_all_expected_fields -v`
Expected: PASS

- [ ] **Step 5: Run full web test file**

Run: `pytest tests/integration/test_web_routes.py -v`
Expected: PASS (7 passed)

- [ ] **Step 6: Commit**

```bash
git add src/web/templates/application_detail.html tests/integration/test_web_routes.py
git commit -m "feat: render full application detail page with provenance"
```

---

### Task 7: Full test suite pass and README instructions

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: nothing new — this task verifies everything from Tasks 1–6
  together.
- Produces: updated `README.md` with a "Web dashboard" section.

- [ ] **Step 1: Run the entire test suite**

Run: `pytest -v`
Expected: all tests pass, including the new
`tests/integration/test_dashboard_service.py`,
`tests/integration/test_application_service.py`, and
`tests/integration/test_web_routes.py`, plus all pre-existing tests
unaffected.

- [ ] **Step 2: Add a "Web dashboard" section to `README.md`**

Read the current `README.md` first to find a sensible insertion point
(after any existing "Running the ingestion CLI" or setup section), then add:

```markdown
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
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add web dashboard run instructions"
```

- [ ] **Step 4: Run `graphify update .` to refresh the code graph**

Run: `graphify update .`
Expected: graph rebuilt reflecting new `src/web` and `src/services` files.

- [ ] **Step 5: Commit graph update**

```bash
git add graphify-out
git commit -m "chore: update graphify graph for web dashboard"
```

---

## Plan Self-Review Notes

- **Spec coverage:** KPI cards, coverage date range, last ingestion
  timestamp (Task 5/2), 3 charts (Task 5/2), filterable/paginated table
  (Task 3/5), detail page with all listed fields (Task 6), provenance
  display (Task 6), filters on canonical field names (Task 3/5), service
  layer split exactly as specified (Task 2/3), dependencies limited to
  fastapi/uvicorn/jinja2 (Task 1), tests for service queries + route smoke
  + 404 + filter correctness + pagination (Tasks 2, 3, 4, 5, 6), README
  section (Task 7). All spec sections have a corresponding task.
- **No placeholders:** all code blocks are complete and runnable; the one
  caveat (Task 3's pagination test `q` value) is resolved inline in Step 2
  of that task rather than left as a TODO.
- **Type/name consistency:** `Application` field names match
  `src/core/models/application.py` exactly across all tasks. Service
  function signatures (`get_summary(db)`, `get_monthly_counts(db)`,
  `get_status_breakdown(db)`, `get_type_breakdown(db)`, `search(db, filters,
  page, page_size)`, `get_by_natural_key(db, planning_authority,
  application_ref)`) are identical wherever referenced in Tasks 2–6.
- **Live-data verification (2026-07-01):** connected to the real dev
  Postgres DB and confirmed: `gen_random_uuid()` works (Postgres 16 has it
  built in); real `planning_status_current` values are
  `Received`/`Granted`/`Refused`/`Withdrawn`/`Invalid` (title case) and real
  `application_type` values are free-text strings like `Permission`,
  `OUTLINE PERMISSION`, `RETENTION` — all test fixtures in Tasks 2, 3, and 6
  were corrected to use these real values instead of placeholder
  `GRANTED`/`REFUSED`/`P`/`E` strings; only 1 of 20,329 real
  `application_ref` values contains a `/` (a stray `TEST/0001` artifact),
  confirming the `:path` converter on the detail route (Task 4) is the
  correct choice and was already handled properly in the original plan.
  Explicit constraints on table ordering (`date_received DESC`), chart
  scope (global, not filter-aware), and filter-input style (plain text, not
  dropdowns) were added to Global Constraints to remove ambiguity flagged
  in review.
