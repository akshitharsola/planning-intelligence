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
