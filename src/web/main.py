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
