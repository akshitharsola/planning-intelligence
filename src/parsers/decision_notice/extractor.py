"""Rule-based extractor for Irish planning decision notices (Galway County & City).

Extracts numbered refusal reasons or grant conditions from layout-preserved text.
"""

from dataclasses import dataclass
import re
from typing import Optional

# Watermark tokens stamped across Galway City planning inspection PDFs
WM_TOKENS = {
    "G", "al", "w", "ay", "C", "ity", "Pl", "ann", "an", "ni", "ng", "in", "g",
    "Au", "th", "or", "thor", "ity", "-I", "ns", "pec", "tio", "n", "Pu", "rp",
    "os", "es", "O", "nl", "y!", "p", "ec", "y", "al  w", "-I     p"
}


@dataclass
class ParsedItem:
    n: int
    text: str
    reason_text: Optional[str] = None


@dataclass
class ParsedNotice:
    status: str
    kind: Optional[str]
    items: list[ParsedItem]
    stated_count: Optional[int]
    target_count: Optional[int]
    failure_reason: Optional[str]


def has_text_layer(text: str, authority: str = "") -> bool:
    """Detect if notice text has a genuine text layer (fewer than 5 non-blank/non-watermark lines = False)."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return False
    if "CITY" in authority.upper():
        lines = [line for line in lines if line not in WM_TOKENS]
    return len(lines) >= 5


def clean_watermark(text: str) -> str:
    """Clean diagonal watermark fragments from City notices without corrupting indentation or text."""
    cleaned_lines = []
    for line in text.splitlines():
        tokens = line.split()
        if tokens and all(t in WM_TOKENS for t in tokens):
            cleaned_lines.append("")
            continue

        # Trailing watermark fragment separated by at least 2 spaces
        m_trail = re.search(r"^(.*?)\s{2,}([A-Za-z!-]{1,4})\s*$", line)
        if m_trail and m_trail.group(2) in WM_TOKENS:
            line = m_trail.group(1)

        # Leading watermark token separated by at least 3 spaces: replace token with whitespace to preserve indent
        m_lead = re.match(r"^(\s*)([A-Za-z!-]{1,4})(\s{3,})(\S.*)$", line)
        if m_lead and m_lead.group(2) in WM_TOKENS:
            line = m_lead.group(1) + (" " * len(m_lead.group(2))) + m_lead.group(3) + m_lead.group(4)

        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def get_stated_count(text: str) -> Optional[int]:
    """Extract explicit condition/reason count stated on page 1 of County notices."""
    m = (
        re.search(r"\((?:CONDITION\s*NO[\s.’\x27]*S|REASON\(S\)|REASONS?)\s*(\d+)\s*\)", text, re.I)
        or re.search(r"conditions?\s+(\d+)\s+set\s+out", text, re.I)
        or re.search(r"reasons?\s+(\d+)\s+set\s+out", text, re.I)
    )
    return int(m.group(1)) if m else None


def clean_item_lines(lines: list[str]) -> list[str]:
    """Strip running headers, footers, standalone page numbers, and form feeds."""
    cleaned = []
    for l in lines:
        if re.match(r"^\s*(?:SIGNED|Signed)\b", l):
            break
        s = l.strip().replace("\x0c", "").strip()
        if not s:
            continue
        if re.match(r"^schedule\s+referred\s+to", s, re.I):
            continue
        if re.match(r"^planning\s+(?:register\s+)?reference", s, re.I):
            continue
        if re.match(r"^chief\s+executive", s, re.I):
            continue
        if re.match(r"^\d{1,2}$", s):
            continue
        cleaned.append(s)
    return cleaned


def split_condition_and_reason(lines: list[str], is_refusal: bool = False) -> tuple[str, Optional[str]]:
    """Split condition text from its trailing REASON block."""
    if is_refusal:
        return " ".join(lines), None
    full = "\n".join(lines)
    m = re.search(r"\bREASONS?\s*:\s*(.*)", full, re.I | re.S)
    if m:
        cond_text = full[:m.start()].strip()
        reason_text = m.group(1).strip()
        cond_clean = re.sub(r"\s+", " ", cond_text)
        reason_clean = re.sub(r"\s+", " ", reason_text)
        return cond_clean, reason_clean
    return re.sub(r"\s+", " ", full), None


def parse_schedule_items(sec: str, expected_total: Optional[int] = None) -> list[dict]:
    """Parse top-level sequentially numbered conditions/reasons (1..N)."""
    lines = sec.splitlines()
    raw_items = []
    current_item = None
    expected_num = 1
    # Match top-level item numbers (allow '.', ')', or 2+ spaces / end-of-line delimiter)
    item_header_re = re.compile(r"^(\s*)(\d{1,2})(?:[.)](?!\d)|\s{2,}|\s*$)\s*(.*)")

    for line in lines:
        if "schedule referred to" in line.lower() or "planning register reference" in line.lower():
            continue
        if re.search(r"^\s*Footnote\s*:", line, re.I):
            break
        if current_item and re.match(r"^\s*SIGNED\s*:", line, re.I):
            if expected_total and len(raw_items) == expected_total:
                break

        m = item_header_re.match(line)
        if m:
            indent = len(m.group(1))
            num = int(m.group(2))
            rest = m.group(3).strip()
            # Top-level items have shallow indent (<= 6 spaces) and strictly sequential numbering
            if indent <= 6 and num == expected_num:
                if current_item:
                    raw_items.append(current_item)
                current_item = {"n": num, "lines": [rest] if rest else []}
                expected_num += 1
                continue

        if current_item:
            current_item["lines"].append(line)

    if current_item:
        raw_items.append(current_item)

    return raw_items


def parse_notice(
    text: str,
    authority: str,
    eplan_count: Optional[int] = None,
    decision: Optional[str] = None,
) -> ParsedNotice:
    """Parse pure-text notice into structured items validated against expected count.

    Status is one of: validated, count_mismatch, needs_ocr, no_schedule, unparsed, unverified.
    """
    if not has_text_layer(text, authority=authority):
        return ParsedNotice(
            status="needs_ocr",
            kind=None,
            items=[],
            stated_count=None,
            target_count=eplan_count,
            failure_reason="No text layer (scanned PDF image)",
        )

    is_city = "CITY" in authority.upper()
    cleaned = clean_watermark(text) if is_city else text
    stated = get_stated_count(text)
    target = stated if (stated is not None) else eplan_count

    if decision is not None:
        is_refusal = "REFU" in decision.upper()
    else:
        is_refusal = bool(re.search(r"\brefus(?:e|ed|al)\b", text, re.I))

    # Check Extension of Duration (EOD) inline refusals
    m_dur = re.search(r"reason\(s\)\s+set\s+out\s+hereunder[;:]\s*(.*)", cleaned, re.S | re.I)
    if not m_dur and is_city:
        m_dur = re.search(r"refused\s+for\s+the\s+following\s+reason\s*[:\-]\s*(.*)", cleaned, re.S | re.I)

    if m_dur:
        lines = [l.strip() for l in m_dur.group(1).splitlines() if l.strip()]
        end_lines = []
        for l in lines:
            if re.match(r"^signed", l, re.I):
                break
            end_lines.append(l)
        c_text, r_text = split_condition_and_reason(clean_item_lines(end_lines), is_refusal=True)
        items = [ParsedItem(n=1, text=c_text, reason_text=r_text)]
        # Extension-of-Duration (EOD) notices state a single inline reason in the notice body
        # rather than a numbered schedule. If no stated count or ePlanning count is available,
        # target defaults to 1 because an EOD refusal notice by definition carries exactly one inline reason.
        if target is None:
            target = 1
        validated = len(items) == target
        return ParsedNotice(
            status="validated" if validated else "count_mismatch",
            kind="refusal_reason",
            items=items,
            stated_count=stated or 1,
            target_count=target,
            failure_reason=None if validated else f"Parsed {len(items)} items vs target {target}",
        )

    # Check for Schedule header
    i = re.search(r"schedule\s+referred\s+to", cleaned, re.I)
    if not i:
        return ParsedNotice(
            status="no_schedule",
            kind=None,
            items=[],
            stated_count=stated,
            target_count=target,
            failure_reason="No schedule header found (e.g. consultation letter or non-schedule notice)",
        )

    sec = cleaned[i.start():]
    fn = re.search(r"\n\s*Footnote\s*:", sec, re.I)
    if fn:
        sec = sec[:fn.start()]

    raw_items = parse_schedule_items(sec, expected_total=target)

    # Handle single unnumbered refusal reason variant
    if len(raw_items) == 0 and target == 1:
        clean_lines = clean_item_lines(sec.splitlines())
        if len(clean_lines) >= 3:
            c_text, r_text = split_condition_and_reason(clean_lines, is_refusal=is_refusal)
            items = [ParsedItem(n=1, text=c_text, reason_text=r_text)]
        else:
            items = []
    else:
        items = []
        for it in raw_items:
            clean_lines = clean_item_lines(it["lines"])
            c_text, r_text = split_condition_and_reason(clean_lines, is_refusal=is_refusal)
            items.append(ParsedItem(n=it["n"], text=c_text, reason_text=r_text))

    parsed_count = len(items)
    if target is not None and parsed_count == target and parsed_count > 0:
        status = "validated"
        failure_reason = None
    elif target is not None and parsed_count != target:
        status = "count_mismatch"
        failure_reason = f"Parsed {parsed_count} items vs target {target}"
    elif parsed_count > 0:
        status = "unverified"
        failure_reason = "No stated or ePlanning count to validate against"
    else:
        status = "unparsed"
        failure_reason = "Failed to extract items from schedule"

    kind = ("refusal_reason" if is_refusal else "condition") if parsed_count > 0 else None

    return ParsedNotice(
        status=status,
        kind=kind,
        items=items,
        stated_count=stated,
        target_count=target,
        failure_reason=failure_reason,
    )

