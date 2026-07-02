"""
Natural-language Q&A over the applications table. Read-only: the LLM only
extracts search filters and summarizes results, it never writes to the DB
or triggers other actions.
"""

from sqlalchemy.orm import Session

from src.services import application_service, dashboard_service
from src.services.llm_client import LLMClient, extract_json, get_llm_client

MAX_RESULTS_FOR_CONTEXT = 20

_FILTER_KEYS = (
    "planning_authority",
    "planning_status_current",
    "application_type",
    "date_received_from",
    "date_received_to",
    "q",
)


def _extraction_prompt(db: Session) -> str:
    authorities = dashboard_service.get_distinct_authorities(db)
    statuses = sorted(r["label"] for r in dashboard_service.get_status_breakdown(db) if r["label"])
    types = sorted(r["label"] for r in dashboard_service.get_type_breakdown(db) if r["label"])
    return (
        "You translate a user's question about Irish planning applications into a JSON "
        "filter object. Reply with ONLY the JSON object, no other text.\n\n"
        "Allowed keys (omit any key you can't confidently determine):\n"
        '  "planning_authority": one of ' + str(authorities) + "\n"
        '  "planning_status_current": one of ' + str(statuses) + "\n"
        '  "application_type": one of ' + str(types) + "\n"
        '  "date_received_from": "YYYY-MM-DD"\n'
        '  "date_received_to": "YYYY-MM-DD"\n'
        '  "q": free-text keyword to search applicant/address/description (e.g. a place name)\n\n'
        "If the question mentions a place name (e.g. a town or area), put it in \"q\". "
        "If a field can't be determined, omit the key entirely rather than guessing."
    )


def _extract_filters(client: LLMClient, db: Session, question: str) -> dict:
    system = _extraction_prompt(db)
    reply = client.chat(system, question)
    parsed = extract_json(reply)
    if not parsed:
        return {}
    return {k: v for k, v in parsed.items() if k in _FILTER_KEYS and v}


def _summarize(client: LLMClient, question: str, filters: dict, rows: list, total: int) -> str:
    if total == 0:
        return "No applications matched your question."

    row_lines = []
    for app in rows[:MAX_RESULTS_FOR_CONTEXT]:
        row_lines.append(
            f"- {app.application_ref} | {app.planning_authority} | {app.applicant_name} | "
            f"{app.site_address} | {app.application_type} | {app.planning_status_current} | "
            f"received {app.date_received}"
        )
    context = "\n".join(row_lines)
    system = (
        "You answer questions about Irish planning applications using only the data "
        "provided below. Be concise (2-4 sentences). Do not invent details not present "
        "in the data. If there are more results than shown, mention the total count."
    )
    user = (
        f"Question: {question}\n"
        f"Total matches: {total}\n"
        f"Showing up to {MAX_RESULTS_FOR_CONTEXT}:\n{context}"
    )
    try:
        return client.chat(system, user)
    except Exception:
        return _fallback_summary(rows, total)


def _fallback_summary(rows: list, total: int) -> str:
    if total == 0:
        return "No applications matched your question."
    names = ", ".join(r.application_ref for r in rows[:5])
    return f"Found {total} matching application(s). Examples: {names}."


def answer_question(db: Session, question: str, client: LLMClient | None = None) -> dict:
    """Returns {"answer": str, "filters": dict, "applications": list, "total": int}."""
    client = client or get_llm_client()

    try:
        filters = _extract_filters(client, db, question)
    except Exception:
        filters = {}

    full_filters = {k: filters.get(k) for k in _FILTER_KEYS}
    rows, total = application_service.search(db, full_filters, page=1, page_size=MAX_RESULTS_FOR_CONTEXT)

    answer = _summarize(client, question, filters, rows, total)

    return {
        "answer": answer,
        "filters": filters,
        "applications": rows,
        "total": total,
    }
