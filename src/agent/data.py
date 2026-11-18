"""Database lookups for the agent. Read-only."""

from typing import Optional

import sqlalchemy as sa
from sqlalchemy.engine import Connection

DOC_TYPE_LABEL = {
    "notification_of_decision": "Notification of Decision",
    "final_grant": "Final Grant",
}

APP_COLUMNS = """a.id, a.planning_authority, a.application_ref, a.application_type, a.development_description,
    a.site_address, a.decision, a.planning_status_current, a.date_received, a.decision_due_date,
    a.decision_date, a.grant_date, a.withdrawn_date, a.expiry_date, a.fi_request_date, a.fi_received_date,
    a.appeal_ref_number, a.appeal_status, a.appeal_decision, a.appeal_decision_date, a.official_detail_url"""

# Latest validated document per application (highest numeric council_doc_id).
LATEST_VALIDATED_DOC = """
    SELECT DISTINCT ON (d.planning_authority, d.application_ref) d.*
      FROM decision_documents d
     WHERE d.status = 'validated'
     ORDER BY d.planning_authority, d.application_ref,
              CASE WHEN d.council_doc_id ~ '^[0-9]+$' THEN d.council_doc_id::bigint ELSE 0 END DESC
"""


def _iso(v):
    return v.isoformat() if hasattr(v, "isoformat") else v


def _row(r) -> dict:
    return {k: _iso(v) for k, v in r._mapping.items() if k != "id"}


def find_applications(conn: Connection, ref: str, authority: Optional[str] = None) -> list[dict]:
    sql = f"SELECT {APP_COLUMNS} FROM dhlgh_applications a WHERE a.application_ref = :ref"
    params = {"ref": ref}
    if authority:
        sql += " AND a.planning_authority = :auth"
        params["auth"] = authority
    return [_row(r) for r in conn.execute(sa.text(sql + " ORDER BY a.planning_authority"), params)]


def decision_items(conn: Connection, authority: str, ref: str) -> tuple[Optional[dict], list[dict]]:
    """Items of the latest validated document, or (None, []) when there is none."""
    doc = conn.execute(
        sa.text(f"SELECT * FROM ({LATEST_VALIDATED_DOC}) v WHERE v.planning_authority=:a AND v.application_ref=:r"),
        {"a": authority, "r": ref},
    ).first()
    if not doc:
        return None, []
    items = conn.execute(
        sa.text("SELECT item_no, kind, text, reason_text FROM decision_items WHERE document_id=:d ORDER BY item_no"),
        {"d": doc.id},
    ).fetchall()
    source = {
        "council_doc_id": doc.council_doc_id,
        "doc_type": DOC_TYPE_LABEL.get(doc.doc_type, doc.doc_type),
        "source_url": doc.source_url,
        "stated_count": doc.stated_count,
        "item_count": len(items),
    }
    return source, [dict(r._mapping) for r in items]


def document_statuses(conn: Connection, authority: str, ref: str) -> list[str]:
    return [r[0] for r in conn.execute(
        sa.text("SELECT status FROM decision_documents WHERE planning_authority=:a AND application_ref=:r"),
        {"a": authority, "r": ref},
    )]


def _filters(authority, year, decision, place, alias="a", month=None) -> tuple[str, dict]:
    where, params = [], {}
    if authority:
        where.append(f"{alias}.planning_authority = :auth"); params["auth"] = authority
    if year and month:
        end_y, end_m = (year + 1, 1) if month == 12 else (year, month + 1)
        where.append(f"{alias}.decision_date >= :y0 AND {alias}.decision_date < :y1")
        params["y0"], params["y1"] = f"{year}-{month:02d}-01", f"{end_y}-{end_m:02d}-01"
    elif year:
        where.append(f"{alias}.decision_date >= :y0 AND {alias}.decision_date < :y1")
        params["y0"], params["y1"] = f"{year}-01-01", f"{year + 1}-01-01"
    elif month:
        where.append(f"extract(month from {alias}.decision_date) = :mon"); params["mon"] = month
    if decision:
        where.append(f"{alias}.decision = :dec"); params["dec"] = decision
    if place:
        where.append(f"{alias}.site_address ILIKE :place"); params["place"] = f"%{place}%"
    return (" AND ".join(where) or "TRUE"), params


def place_exists(conn: Connection, place: str) -> bool:
    return bool(conn.execute(
        sa.text("SELECT 1 FROM dhlgh_applications WHERE site_address ILIKE :p LIMIT 1"), {"p": f"%{place}%"}
    ).first())


def _tsquery(groups: list[list[str]]) -> str:
    """Words are ANDed; synonyms of one word are ORed: (wastewater|septic) & road."""
    clean = lambda w: "".join(ch for ch in w if ch.isalnum())
    parts = []
    for g in groups:
        alts = [clean(w) for w in g if clean(w)]
        if alts:
            parts.append("(" + " | ".join(alts) + ")")
    return " & ".join(parts)


def search_items(conn: Connection, groups: list[list[str]], authority=None, year=None, decision=None, place=None,
                 kind: Optional[str] = None, limit: int = 8, month: Optional[int] = None) -> tuple[int, list[dict]]:
    """Full-text search over validated reasons/conditions; one best match per application,
    taken from that application's latest validated document."""
    tsq = _tsquery(groups)
    if not tsq:
        return 0, []
    where, params = _filters(authority, year, decision, place, month=month)
    params.update({"tsq": tsq, "limit": limit})
    kind_sql = ""
    if kind:
        kind_sql = "AND i.kind = :kind"; params["kind"] = kind
    sql = f"""
        WITH q AS (SELECT to_tsquery('english', :tsq) AS query),
        matched AS (            -- uses the GIN index on search_vector first
          SELECT i.document_id, i.item_no, i.kind, i.text, i.reason_text, ts_rank(i.search_vector, q.query) AS rank
            FROM decision_items i, q
           WHERE i.search_vector @@ q.query {kind_sql}
        ),
        hits AS (
          SELECT a.application_ref, a.planning_authority, a.site_address, a.decision, a.decision_date,
                 a.development_description, d.council_doc_id, d.doc_type, d.source_url,
                 m.item_no, m.kind, m.text, m.reason_text, m.rank,
                 row_number() OVER (PARTITION BY a.planning_authority, a.application_ref
                                    ORDER BY m.rank DESC, m.item_no) AS rn
            FROM matched m
            JOIN decision_documents d ON d.id = m.document_id AND d.status = 'validated'
            JOIN dhlgh_applications a ON a.planning_authority = d.planning_authority
                                     AND a.application_ref = d.application_ref
           WHERE {where}
             AND NOT EXISTS (   -- only the latest validated document of the application
               SELECT 1 FROM decision_documents n
                WHERE n.planning_authority = d.planning_authority AND n.application_ref = d.application_ref
                  AND n.status = 'validated' AND n.id <> d.id
                  AND n.council_doc_id ~ '^[0-9]+$' AND d.council_doc_id ~ '^[0-9]+$'
                  AND n.council_doc_id::bigint > d.council_doc_id::bigint)
        ),
        best AS (SELECT *, count(*) OVER () AS total FROM hits WHERE rn = 1)
        SELECT b.*, ts_headline('english', b.text, (SELECT query FROM q),
                                'MaxWords=40, MinWords=18, StartSel=<<, StopSel=>>') AS snippet
          FROM best b ORDER BY rank DESC, decision_date DESC NULLS LAST LIMIT :limit"""
    rows = conn.execute(sa.text(sql), params).fetchall()
    total = rows[0].total if rows else 0
    out = []
    for r in rows:
        d = {k: _iso(v) for k, v in r._mapping.items() if k not in ("rank", "rn", "total")}
        d["doc_type"] = DOC_TYPE_LABEL.get(d["doc_type"], d["doc_type"])
        out.append(d)
    return total, out


def list_applications(conn: Connection, authority=None, year=None, decision=None, place=None, limit: int = 10,
                      month: Optional[int] = None):
    where, params = _filters(authority, year, decision, place, month=month)
    params["limit"] = limit
    total = conn.execute(sa.text(f"SELECT count(*) FROM dhlgh_applications a WHERE {where}"), params).scalar()
    rows = conn.execute(sa.text(f"""
        SELECT a.planning_authority, a.application_ref, a.site_address, a.decision, a.decision_date,
               a.application_type, a.development_description,
               EXISTS (SELECT 1 FROM decision_documents d WHERE d.planning_authority=a.planning_authority
                         AND d.application_ref=a.application_ref AND d.status='validated') AS has_reasons
          FROM dhlgh_applications a WHERE {where}
         ORDER BY a.decision_date DESC NULLS LAST, a.application_ref LIMIT :limit"""), params)
    return total, [{k: _iso(v) for k, v in r._mapping.items()} for r in rows]


def count_by_decision(conn: Connection, authority=None, year=None, place=None, month: Optional[int] = None) -> dict:
    where, params = _filters(authority, year, None, place, month=month)
    rows = conn.execute(sa.text(f"""
        SELECT coalesce(a.decision, 'NO DECISION YET') AS decision, count(*) FROM dhlgh_applications a
         WHERE {where} GROUP BY 1 ORDER BY 2 DESC"""), params)
    return {r[0]: r[1] for r in rows}


def coverage(conn: Connection) -> dict:
    row = conn.execute(sa.text("""
        SELECT count(DISTINCT (d.planning_authority, d.application_ref)) FILTER (WHERE d.status='validated') AS apps,
               min(a.decision_date) FILTER (WHERE d.status='validated') AS first,
               max(a.decision_date) FILTER (WHERE d.status='validated') AS last
          FROM decision_documents d LEFT JOIN dhlgh_applications a ON a.id = d.dhlgh_application_id""")).first()
    total = conn.execute(sa.text("SELECT count(*) FROM dhlgh_applications")).scalar()
    return {"applications_total": total, "applications_with_reasons": row.apps,
            "reasons_from": _iso(row.first), "reasons_to": _iso(row.last)}


def latest_year_for_month(conn: Connection, month: int, authority=None, decision=None, place=None) -> Optional[int]:
    """Most recent year that has decisions in this month (for "refused in March" with no year)."""
    where, params = _filters(authority, None, decision, place, month=month)
    return conn.execute(sa.text(f"SELECT max(extract(year from a.decision_date))::int FROM dhlgh_applications a WHERE {where}"), params).scalar()


def items_for_scope(conn: Connection, authority=None, year=None, decision=None, place=None, month=None,
                    limit: int = 10) -> tuple[int, int, list[dict]]:
    """Applications in scope with their checked reasons/conditions (latest validated document).

    Returns (applications in scope, of which with checked text, rows for up to `limit` applications)."""
    where, params = _filters(authority, year, decision, place, month=month)
    params["limit"] = limit
    totals = conn.execute(sa.text(f"""
        SELECT count(*) AS total,
               count(*) FILTER (WHERE EXISTS (SELECT 1 FROM decision_documents d WHERE d.planning_authority=a.planning_authority
                                 AND d.application_ref=a.application_ref AND d.status='validated')) AS with_text
          FROM dhlgh_applications a WHERE {where}"""), params).first()
    apps = conn.execute(sa.text(f"""
        SELECT a.planning_authority, a.application_ref, a.site_address, a.decision, a.decision_date,
               a.application_type, a.development_description, v.id AS doc_id, v.council_doc_id, v.doc_type, v.source_url
          FROM dhlgh_applications a
          JOIN ({LATEST_VALIDATED_DOC}) v ON v.planning_authority = a.planning_authority AND v.application_ref = a.application_ref
         WHERE {where}
         ORDER BY a.decision_date DESC NULLS LAST, a.application_ref LIMIT :limit"""), params).fetchall()
    out = []
    for r in apps:
        items = conn.execute(sa.text(
            "SELECT item_no, kind, text, reason_text FROM decision_items WHERE document_id=:d ORDER BY item_no"),
            {"d": r.doc_id}).fetchall()
        row = {k: _iso(v) for k, v in r._mapping.items() if k != "doc_id"}
        row["doc_type"] = DOC_TYPE_LABEL.get(row["doc_type"], row["doc_type"])
        row["items"] = [dict(i._mapping) for i in items]
        out.append(row)
    return totals.total, totals.with_text, out
