"""Planning Q&A agent: question -> structured, cited answer. Facts come only from the DB."""

from datetime import date
from typing import Callable, Optional

from sqlalchemy.engine import Connection

from src.agent import data
from src.agent.question import COUNTY, CITY, ParsedQuestion, parse_question

NOT_IN_RECORDS = "The reasons for this decision are not in our records."

EXAMPLES = [
    "Why was application 2660494 refused?",
    "What conditions apply to 2661255?",
    "Status of application 2560749",
    "Refusals about wastewater in 2026",
    "Conditions about flooding in Oughterard",
    "How many applications were refused in 2025?",
    "Refused applications in Clifden in 2026",
]


def _fmt_date(v: Optional[str]) -> Optional[str]:
    if not v:
        return None
    d = date.fromisoformat(v[:10])
    return f"{d.day} {d.strftime('%b %Y')}"


def _decision_phrase(app: dict) -> str:
    dec, when = app.get("decision"), _fmt_date(app.get("decision_date"))
    if dec == "REFUSED":
        return f"Refused on {when}." if when else "Refused."
    if dec == "CONDITIONAL":
        return f"Granted with conditions on {when}." if when else "Granted with conditions."
    if dec == "UNCONDITIONAL":
        return f"Granted without conditions on {when}." if when else "Granted without conditions."
    status = (app.get("planning_status_current") or "").strip()
    return f"No decision recorded yet (status: {status.lower() or 'unknown'})."


def _why_missing(conn: Connection, app: dict) -> str:
    if app["planning_authority"] == CITY:
        return "Reasons and conditions are only available for Galway County Council decisions at the moment."
    year = int(app["decision_date"][:4]) if app.get("decision_date") else None
    if year and year < 2025:
        return f"Reasons and conditions are only available for decisions made in 2025 and 2026 (this one was decided in {year})."
    statuses = set(data.document_statuses(conn, app["planning_authority"], app["application_ref"]))
    if "needs_ocr" in statuses:
        return "The council's notice is a scanned image that we have not yet read."
    if "count_mismatch" in statuses:
        return "We could not confirm the full list against the count the council states, so we don't show it."
    if not statuses:
        return "No decision notice was found on the council's document page."
    return "We could not extract a checked list from the council's notice."


def _application_answer(conn: Connection, q: ParsedQuestion, app: dict) -> dict:
    ref, auth = app["application_ref"], app["planning_authority"]
    source, items = (None, [])
    if app.get("decision") in ("REFUSED", "CONDITIONAL"):
        source, items = data.decision_items(conn, auth, ref)

    lines = [f"Application {ref} ({auth}). {_decision_phrase(app)}"]
    note = None
    if app.get("decision") == "REFUSED":
        if items:
            lines.append(f"The council gave {len(items)} reason{'s' if len(items) != 1 else ''} for refusal, quoted below from its {source['doc_type']}.")
        else:
            lines.append(NOT_IN_RECORDS); note = _why_missing(conn, app)
    elif app.get("decision") == "CONDITIONAL":
        if q.wants_reasons and not q.wants_conditions and not (items and items[0]["kind"] == "refusal_reason"):
            lines.append("It was not refused, so there are no refusal reasons." + (" Its conditions are below." if items else ""))
        if items:
            if items[0]["kind"] == "refusal_reason":
                lines.append(f"Note: the national register records this as granted, but the council's {source['doc_type']} "
                             f"is a refusal{' of the extension' if 'EXTENSION' in (app.get('application_type') or '') else ''}. "
                             "The council's reason is quoted below.")
            else:
                lines.append(f"The permission carries {len(items)} condition{'s' if len(items) != 1 else ''}, quoted below from the council's {source['doc_type']}.")
        else:
            lines.append("The conditions for this decision are not in our records."); note = _why_missing(conn, app)
    elif app.get("decision") == "UNCONDITIONAL":
        lines.append("There are no conditions to show.")
    return {
        "type": "application",
        "message": " ".join(lines),
        "note": note,
        "application": app,
        "items": items,
        "source": source,
    }


def answer_question(conn: Connection, text: str,
                    interpret: Optional[Callable[[str, ParsedQuestion], ParsedQuestion]] = None) -> dict:
    q = parse_question(text)
    if interpret and not q.refs and not q.is_help:
        try:
            q = interpret(text, q)
        except Exception:
            pass  # the rules-based reading stands
    result = _answer(conn, q)
    result["parsed"] = q.as_dict()
    result["question"] = text
    return result


def _answer(conn: Connection, q: ParsedQuestion) -> dict:
    if q.is_help or not q.text:
        return {"type": "help", "message": "Ask about a Galway planning application by its reference number, or search the councils' reasons and conditions by topic, place and year.", "suggestions": EXAMPLES}

    if q.place and not data.place_exists(conn, q.place):
        return {"type": "not_found", "message": f"I couldn't find any applications with \"{q.place}\" in the address.", "suggestions": EXAMPLES[:4]}

    if q.refs:
        ref = q.refs[0]
        apps = data.find_applications(conn, ref, q.authority)
        if not apps:
            where = f" in {q.authority}" if q.authority else ""
            return {"type": "not_found", "message": f"There is no application {ref}{where} in our Galway records.", "suggestions": EXAMPLES[:3]}
        if len(apps) > 1:
            return {
                "type": "clarify",
                "message": f"Reference {ref} exists in both Galway County Council and Galway City Council. Which one do you mean?",
                "suggestions": [f"County application {ref}", f"City application {ref}"],
                "applications": apps,
            }
        return _application_answer(conn, q, apps[0])

    kind = None
    if q.decision == "REFUSED":
        kind = "refusal_reason"
    elif q.decision == "CONDITIONAL" or q.wants_conditions:
        kind = "condition"

    if q.wants_count:
        if q.topic_terms:
            total, _ = data.search_items(conn, q.topic_groups, q.authority, q.year, q.decision, q.place, kind, limit=1)
            what = {"refusal_reason": "refused applications", "condition": "granted applications"}.get(kind, "applications")
            return {"type": "count", "message": f"{total} {what} have a {'reason' if kind == 'refusal_reason' else 'reason or condition'} mentioning \"{' '.join(q.topic_terms)}\"{_scope(q)}.",
                    "note": "Counted from checked reasons and conditions (Galway County, 2025–2026).", "counts": {"matching applications": total}}
        counts = data.count_by_decision(conn, q.authority, q.year, q.place)
        where = "" if q.authority else " across Galway County and City councils"
        if q.decision:
            n = counts.get(q.decision, 0)
            label = {"REFUSED": "refused", "CONDITIONAL": "granted with conditions"}[q.decision]
            return {"type": "count", "message": f"{n:,} applications were {label}{_scope(q)}{where}.", "counts": counts}
        return {"type": "count", "message": f"{sum(counts.values()):,} applications{_scope(q)}{where}.", "counts": counts}

    if q.topic_terms:
        total, results = data.search_items(conn, q.topic_groups, q.authority, q.year, q.decision, q.place, kind)
        if not total:
            return {"type": "search", "message": f"No checked reasons or conditions mention \"{' '.join(q.topic_terms)}\"{_scope(q)}.",
                    "note": "Reasons and conditions cover Galway County decisions from 2025 and 2026.", "results": [], "total": 0}
        shown = min(total, len(results))
        return {"type": "search", "message": f"{total} application{'s' if total != 1 else ''} with a matching {'refusal reason' if kind == 'refusal_reason' else 'condition' if kind == 'condition' else 'reason or condition'}{_scope(q)}. Showing the {shown} best matches.",
                "results": results, "total": total}

    if q.decision or q.year or q.place or q.authority:
        total, rows = data.list_applications(conn, q.authority, q.year, q.decision, q.place)
        return {"type": "list", "message": f"{total:,} applications{_scope(q)}{'' if q.authority else ' (Galway County and City)'}. The most recent are listed below.", "results": rows, "total": total}

    return {"type": "help", "message": "I couldn't tell what you're looking for. Try an application number, or a topic with a place or year.", "suggestions": EXAMPLES}


def _scope(q: ParsedQuestion) -> str:
    parts = []
    if q.decision and not q.wants_count and not q.topic_terms:
        parts.append({"REFUSED": "refused", "CONDITIONAL": "granted with conditions"}[q.decision])
    if q.place:
        parts.append(f"in {q.place}")
    if q.authority:
        parts.append(f"({q.authority})")
    if q.year:
        parts.append(f"in {q.year}")
    return (" " + " ".join(parts)) if parts else ""
