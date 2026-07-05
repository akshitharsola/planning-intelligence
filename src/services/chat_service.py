"""
Natural-language Q&A over the applications table. Read-only: the LLM only
extracts search filters and summarizes results, it never writes to the DB
or triggers other actions.
"""

from datetime import date

from sqlalchemy.orm import Session

from src.services import application_service, dashboard_service
from src.services.llm_client import LLMClient, extract_json, get_llm_client

MAX_RESULTS_FOR_CONTEXT = 20


def _today() -> date:
    return date.today()

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
        f"Today's date is {_today().isoformat()}. Resolve relative date phrases "
        "like 'last month', 'this year', or 'last week' against this date, not "
        "your training data.\n\n"
        "You translate a user's question about Irish planning applications into a JSON "
        "filter object. Reply with ONLY the JSON object, no other text.\n\n"
        "Allowed keys (omit any key you can't confidently determine):\n"
        '  "planning_authority": one of ' + str(authorities) + "\n"
        '  "planning_status_current": one of ' + str(statuses) + "\n"
        '  "application_type": one of ' + str(types) + "\n"
        '  "date_received_from": "YYYY-MM-DD"\n'
        '  "date_received_to": "YYYY-MM-DD"\n'
        '  "q": one or more space-separated keywords to search applicant/address/description '
        '(e.g. a place name); every keyword must match, so only include words that should ALL '
        "be present\n\n"
        "If the question mentions a place name (e.g. a town or area), put it ONLY in \"q\" "
        "-- do not also guess \"planning_authority\" from the place name, even if you know "
        "which council the place falls under. Only set \"planning_authority\" if the "
        "question explicitly names a council. "
        "Only set \"application_type\" if the question explicitly names a type (e.g. "
        "\"permission\", \"retention\") -- never guess a type just because the question "
        "mentions an application number, applicant name, or address; omit the key if the "
        "question doesn't say what type it is. "
        "Only set \"planning_status_current\" if the question explicitly names a status "
        "(e.g. \"granted\", \"refused\", \"withdrawn\") -- never guess a status, and never "
        "use \"unknown\" or any other word not in the allowed list above, just because the "
        "question asks what the status IS; asking for the status means the field should "
        "be omitted, not guessed. "
        "If the question includes an application reference number (e.g. \"26/20\" or "
        "\"2661040\"), always include that exact number as one of the keywords in \"q\", "
        "in addition to any applicant name also mentioned. "
        "Do not put dates or date phrases inside \"q\" -- always express any time range "
        "using \"date_received_from\" / \"date_received_to\" instead, and never combine "
        "a place name and a date into one \"q\" string. "
        "If a field can't be determined, omit the key entirely rather than guessing.\n\n"
        "Examples:\n"
        f'  Question: "What\'s new in Tuam for last month"\n'
        '  Reply: {"q": "Tuam", "date_received_from": "<first day of last month>", '
        '"date_received_to": "<last day of last month>"}\n'
        '  Question: "What\'s the status of application 26/20 for Mr Kevin Burke"\n'
        '  Reply: {"q": "26/20 Kevin Burke"}\n'
    )


def _extract_filters(client: LLMClient, db: Session, question: str) -> dict:
    system = _extraction_prompt(db)
    reply = client.chat(system, question)
    parsed = extract_json(reply)
    if not parsed:
        return {}
    filters = {k: v for k, v in parsed.items() if k in _FILTER_KEYS and v}

    enum_filters = {
        "planning_authority": dashboard_service.get_distinct_authorities(db),
        "planning_status_current": [
            r["label"] for r in dashboard_service.get_status_breakdown(db) if r["label"]
        ],
        "application_type": [
            r["label"] for r in dashboard_service.get_type_breakdown(db) if r["label"]
        ],
    }
    for key, allowed_values in enum_filters.items():
        if key in filters and filters[key] not in set(allowed_values):
            del filters[key]

    return filters


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
        "in the data. If total matches exceeds the number of rows shown, explicitly say "
        "these are only a few examples out of the total, not the full list."
    )
    user = (
        f"Question: {question}\n"
        f"Total matches: {total}\n"
        f"Rows shown below: {min(total, MAX_RESULTS_FOR_CONTEXT)} of {total}\n"
        f"{context}"
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


_UNAVAILABLE_MESSAGE = (
    "The AI assistant is temporarily unavailable, so your question couldn't be "
    "answered. Please try again in a moment."
)


def answer_question(db: Session, question: str, client: LLMClient | None = None) -> dict:
    """Returns {"answer": str, "filters": dict, "applications": list, "total": int}."""
    client = client or get_llm_client()

    try:
        filters = _extract_filters(client, db, question)
    except Exception:
        return {
            "answer": _UNAVAILABLE_MESSAGE,
            "filters": {},
            "applications": [],
            "total": 0,
        }

    full_filters = {k: filters.get(k) for k in _FILTER_KEYS}
    rows, total = application_service.search(db, full_filters, page=1, page_size=MAX_RESULTS_FOR_CONTEXT)

    answer = _summarize(client, question, filters, rows, total)

    return {
        "answer": answer,
        "filters": filters,
        "applications": rows,
        "total": total,
    }
