"""Standalone demo web app for the planning Q&A agent (separate from src/web).

Run:  python scripts/run_agent_demo.py   then open http://localhost:8020
"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.agent import data
from src.agent.agent import EXAMPLES, answer_question
from src.agent.llm import make_ollama_interpreter, ollama_available
from src.core.db.session import engine

PAGE = Path(__file__).with_name("demo.html")

app = FastAPI(title="Galway Planning Assistant (demo)")

_use_llm = os.getenv("AGENT_USE_OLLAMA", "auto").lower()
_interpreter = None
if _use_llm in ("auto", "1", "true", "yes") and ollama_available():
    _interpreter = make_ollama_interpreter()


class Ask(BaseModel):
    question: str


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return PAGE.read_text(encoding="utf-8")


@app.get("/api/info")
def info() -> dict:
    with engine.connect() as conn:
        cov = data.coverage(conn)
    return {**cov, "examples": EXAMPLES, "llm": bool(_interpreter)}


@app.post("/api/ask")
def ask(body: Ask) -> dict:
    question = body.question.strip()[:300]
    with engine.connect() as conn:
        return answer_question(conn, question, interpret=_interpreter)
