"""Optional Ollama step: turn a free-form question into search filters.

The model never writes answers. It only returns JSON filters, which are validated and
merged into the rules-based reading (rules win where they found something). If Ollama
is not running, the agent works the same without it.
"""

import json
import os
import re
from dataclasses import replace
from typing import Optional

import requests

from src.agent.question import COUNTY, CITY, TOPIC_SYNONYMS, ParsedQuestion

PROMPT = """You turn questions about Galway planning applications into JSON search filters.
Return ONLY a JSON object with these keys (use null when not mentioned):
  "decision": "REFUSED" or "CONDITIONAL" or null
  "year": a 4-digit year or null
  "place": a town or townland name or null
  "council": "county" or "city" or null
  "topic": up to 3 short keywords about the subject (e.g. ["wastewater"], ["road", "safety"]) or []
  "count": true if the user asks how many, else false
Question: {question}
JSON:"""


def ollama_available(base_url: Optional[str] = None, timeout: float = 1.5) -> bool:
    url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
    try:
        return requests.get(f"{url}/api/tags", timeout=timeout).ok
    except requests.RequestException:
        return False


def make_ollama_interpreter(base_url: Optional[str] = None, model: Optional[str] = None, timeout: float = 30.0,
                            post=requests.post):
    url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
    model = model or os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    def interpret(question: str, q: ParsedQuestion) -> ParsedQuestion:
        resp = post(f"{url}/api/generate", json={
            "model": model, "prompt": PROMPT.format(question=question), "format": "json", "stream": False,
            "options": {"temperature": 0},
        }, timeout=timeout)
        resp.raise_for_status()
        out = json.loads(resp.json().get("response", "{}"))
        return merge_llm_filters(q, out)

    return interpret


def merge_llm_filters(q: ParsedQuestion, out: dict) -> ParsedQuestion:
    """Fill only what the rules left empty, and only with values that pass validation."""
    upd = {}
    dec = out.get("decision")
    if not q.decision and dec in ("REFUSED", "CONDITIONAL"):
        upd["decision"] = dec
    year = out.get("year")
    if not q.year and isinstance(year, int) and 2000 <= year <= 2035:
        upd["year"] = year
    place = out.get("place")
    if not q.place and isinstance(place, str) and re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóú'’ \-]{2,40}", place.strip()):
        upd["place"] = place.strip()
    council = out.get("council")
    if not q.authority and council in ("county", "city"):
        upd["authority"] = COUNTY if council == "county" else CITY
    topic = out.get("topic")
    if not q.topic_terms and isinstance(topic, list):
        words = [w.lower() for w in topic if isinstance(w, str) and re.fullmatch(r"[A-Za-z\-]{3,30}", w)][:3]
        if words:
            upd["topic_terms"] = words
            upd["topic_groups"] = [TOPIC_SYNONYMS.get(w, [w]) for w in words]
    if out.get("count") is True:
        upd["wants_count"] = True
    return replace(q, **upd) if upd else q
