from datetime import date
from pathlib import Path
from urllib.parse import urlencode

from fastapi import Depends, FastAPI, HTTPException, Query, Request
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


def _replace_param(query_params, key, value):
    merged = dict(query_params)
    merged[key] = value
    return urlencode(merged)


templates.env.filters["replace_param"] = _replace_param


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
