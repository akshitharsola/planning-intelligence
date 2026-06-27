"""
Location extraction for Galway descriptions — ported from duffy's
location_extractor.py. Galway-specific area gazetteer; future regions
get their own gazetteer module under src/core/normalization/.
"""

import re

GALWAY_AREAS = [
    "salthill", "knocknacarra", "eyre square", "shop street", "quay street",
    "mainguard street", "dominick street", "abbeygate", "high street",
    "bohermore", "shantalla", "woodquay", "mervue", "doughiska",
    "ballybane", "ballymoneen", "castlegar", "tuam road", "headford road",
    "westside", "rahoon", "corrib", "moycullen road", "barna road",
    "upper salthill", "lower salthill", "renmore", "merlin park",
    "ballybrit", "briarhill", "parkmore", "coolough", "coolagh",
    "newcastle", "dangan", "upper newcastle", "lower newcastle",
    "bushypark", "menlo", "terryland", "wellpark", "kingston",
    "clybaun", "barna", "tuam road industrial", "briarhill business park",
    "galway technology park", "parkmore industrial",
    "galway city", "galway", "co. galway",
]

_EIRCODE_RE = re.compile(r"\bH\d{2}\s*[A-Z0-9]{4}\b", re.IGNORECASE)
_AT_RE = re.compile(
    r"\b(?:at|on lands at|located at|situate at|situate[d]? at|at lands at)\s+",
    re.IGNORECASE,
)


def extract_location(description: str) -> dict:
    if not description:
        return {"area": "", "address": "", "eircode": ""}
    return {
        "area": _extract_area(description),
        "address": _extract_address(description),
        "eircode": _extract_eircode(description),
    }


def _extract_eircode(text: str) -> str:
    m = _EIRCODE_RE.search(text)
    if m:
        raw = m.group(0).upper().replace(" ", "")
        return raw[:3] + " " + raw[3:]
    return ""


def _extract_area(text: str) -> str:
    text_lower = text.lower()
    for area in GALWAY_AREAS:
        if area in text_lower:
            idx = text_lower.find(area)
            return text[idx: idx + len(area)].title()
    return "Galway"


def _extract_address(text: str) -> str:
    matches = list(_AT_RE.finditer(text))
    if matches:
        candidate = text[matches[-1].end():].strip()
        candidate = re.split(r"[\n\r]", candidate)[0].strip()
        candidate = re.sub(r"\s+", " ", candidate)
        if 5 < len(candidate) < 200:
            return candidate
    parts = re.split(r"\.\s+", text)
    for part in reversed(parts):
        part = part.strip()
        if _looks_like_address(part):
            return re.sub(r"\s+", " ", part)[:200]
    return text.strip()[-120:].strip()


def _looks_like_address(text: str) -> bool:
    text_lower = text.lower()
    has_area = any(a in text_lower for a in GALWAY_AREAS)
    has_road = bool(re.search(
        r"\b(road|street|avenue|close|place|lane|drive|park|way|crescent|court|"
        r"rise|grove|view|heights|gardens|estate|terrace|row|square)\b",
        text_lower))
    short_enough = len(text) < 180
    starts_with_verb = bool(re.match(
        r"^(to |for |the |a |an |permission|construction|retention|demolition|"
        r"change|development|proposed|planning)", text_lower))
    return (has_area or has_road) and short_enough and not starts_with_verb
