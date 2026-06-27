"""
Galway City weekly-list PDF parser — first concrete implementation of the
pdf_table_lines parser family. Ported from duffy's pdf_extractor.py.
"""

import logging
import re
from pathlib import Path
from typing import Optional

import pdfplumber

logger = logging.getLogger(__name__)

_SETTINGS_LINES = {
    "vertical_strategy": "lines",
    "horizontal_strategy": "lines",
    "snap_tolerance": 5,
    "join_tolerance": 3,
    "edge_min_length": 10,
    "min_words_vertical": 1,
}
_SETTINGS_TEXT = {
    "vertical_strategy": "text",
    "horizontal_strategy": "lines",
    "snap_tolerance": 5,
    "join_tolerance": 3,
}

_BOILERPLATE_FRAGMENTS = [
    "section 34 of",
    "data protection act",
    "personal details of",
    "freedom of information",
    "g a p p l i c a t i o n",
    "ceived from",
    "may be granted or refused",
    "cts 1988",
    "a p p l i c a t i o n s",
]

_HEADER_FRAGMENTS = [
    "file", "applicant", "app", "date", "description",
    "location", "eis", "prot", "ipc", "waste", "decision",
    "cert", "m.o", "number", "type",
]


def extract_planning_table(pdf_path: Path, column_map: dict) -> list[dict]:
    """Open a PDF and extract all table rows as a list of dicts keyed by
    column_map's values. Returns [] if extraction yields nothing useful."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_rows = _extract_rows(pdf, _SETTINGS_LINES)
            if not all_rows:
                all_rows = _extract_rows(pdf, _SETTINGS_TEXT)
    except Exception as exc:
        logger.error(f"Failed to open/parse {pdf_path}: {exc}")
        return []

    if not all_rows:
        logger.warning(f"No table data extracted from {pdf_path.name}")
        return []

    return _normalise_rows(all_rows, column_map)


def _extract_rows(pdf: "pdfplumber.PDF", settings: dict) -> list[list]:
    all_rows: list[list] = []
    header: Optional[list] = None

    for page in pdf.pages:
        tables = page.extract_tables(table_settings=settings)
        for table in tables or []:
            if not table:
                continue
            rows = [_clean_cells(row) for row in table if row]
            if header is None:
                for i, row in enumerate(rows):
                    if _looks_like_header(row):
                        header = row
                        all_rows.extend(rows[i:])
                        break
                else:
                    all_rows.extend(rows)
            else:
                for row in rows:
                    if not _is_duplicate_header(row, header):
                        all_rows.append(row)
    return all_rows


def _clean_cells(row: list) -> list:
    cleaned = []
    for cell in row:
        cleaned.append("" if cell is None else re.sub(r"\s+", " ", str(cell)).strip())
    return cleaned


def _looks_like_header(row: list) -> bool:
    text = " ".join(str(c).lower() for c in row if c)
    hits = sum(1 for frag in _HEADER_FRAGMENTS if frag in text)
    return hits >= 2


def _is_duplicate_header(row: list, header: list) -> bool:
    if len(row) != len(header):
        return False
    return all(_norm(a) == _norm(b) for a, b in zip(row, header))


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s).lower()).strip()


def _normalise_rows(raw_rows: list[list], column_map: dict) -> list[dict]:
    if not raw_rows:
        return []

    header_idx = None
    for i, row in enumerate(raw_rows):
        if _looks_like_header(row):
            header_idx = i
            break
    if header_idx is None:
        logger.warning("Could not identify header row; skipping normalisation.")
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
            if any(_is_boilerplate(record.get(f, "")) for f in
                   ("file_number", "applicant", "description")):
                continue
            records.append(record)
    return records


def _is_boilerplate(text: str) -> bool:
    t = text.lower()
    return any(f in t for f in _BOILERPLATE_FRAGMENTS)


def _map_column(raw: str, column_map: dict) -> str:
    key = re.sub(r"\s+", " ", raw.lower()).strip().rstrip(".")
    if key in column_map:
        return column_map[key]
    for k, v in column_map.items():
        if k in key or key in k:
            return v
    return re.sub(r"[^a-z0-9]+", "_", key).strip("_")
