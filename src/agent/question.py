"""Rule-based question understanding. Deterministic, so the demo never guesses."""

from dataclasses import dataclass, field
import re
from typing import Optional

COUNTY = "Galway County Council"
CITY = "Galway City Council"

STOPWORDS = set(
    """a an the of for to in on at by with about and or is are was were be been being do does did
    what which who whom whose why how when where show me list give tell find any all some
    there their this that these those it its i we you my our your please can could would should
    many much number count total planning application applications app apps ref reference
    permission permissions decision decisions decided status details info information
    galway county city council co year years since during between from than more most
    reason reasons refused refusal refusals rejected reject rejection turned down granted grant
    grants approved approval approve conditions condition conditional
    near around within get got have has had give given also only just like such
    mention mentions mentioning apply applies applied relating related regarding concerning involving
    contain contains containing say says said mentioned recent latest
    january february march april may june july august september october november december
    jan feb mar apr jun jul aug sep sept oct nov dec month months last tell
    s t""".split()
)

TOPIC_SYNONYMS = {
    "wastewater": ["wastewater", "septic", "percolation", "effluent", "treatment"],
    "sewage": ["sewage", "septic", "wastewater", "effluent"],
    "septic": ["septic", "percolation", "wastewater"],
    "flood": ["flood", "flooding"],
    "flooding": ["flood", "flooding"],
    "traffic": ["traffic", "road", "sightline", "sightlines"],
    "sightlines": ["sightline", "sightlines", "visibility"],
    "parking": ["parking", "car"],
    "heritage": ["heritage", "protected", "archaeological", "archaeology"],
    "archaeology": ["archaeological", "archaeology", "monument"],
    "landscape": ["landscape", "visual", "scenic"],
    "housing": ["housing", "dwelling", "house"],
    "ecology": ["ecology", "habitat", "bat", "bats", "species"],
}


@dataclass
class ParsedQuestion:
    text: str
    refs: list[str] = field(default_factory=list)
    authority: Optional[str] = None
    year: Optional[int] = None
    decision: Optional[str] = None  # "REFUSED" | "CONDITIONAL"
    place: Optional[str] = None
    topic_terms: list[str] = field(default_factory=list)  # words as asked, for display
    topic_groups: list[list[str]] = field(default_factory=list)  # each word with its synonyms
    wants_count: bool = False
    wants_reasons: bool = False
    wants_conditions: bool = False
    month: Optional[int] = None
    asks_item_text: bool = False  # "why", "reasons", "conditions": show the wording, not just a list
    is_help: bool = False

    def as_dict(self) -> dict:
        return {
            "refs": self.refs, "authority": self.authority, "year": self.year, "decision": self.decision,
            "month": self.month, "place": self.place, "topic_terms": self.topic_terms, "wants_count": self.wants_count,
            "wants_reasons": self.wants_reasons, "wants_conditions": self.wants_conditions,
        }


REF_CONTEXT_RE = re.compile(r"\b(?:ref(?:erence)?|application|app|file|no\.?|number|#)\s*[:#]?\s*(\d{3,8})\b", re.I)
NUMBER_RE = re.compile(r"(?<![\d/])(\d{3,8})(?![\d/])")
YEAR_RE = re.compile(r"\b(20[0-3]\d)\b")
MONTHS = {name: i for i, names in enumerate([
    ("january", "jan"), ("february", "feb"), ("march", "mar"), ("april", "apr"), ("may",),
    ("june", "jun"), ("july", "jul"), ("august", "aug"), ("september", "sep", "sept"),
    ("october", "oct"), ("november", "nov"), ("december", "dec")], start=1) for name in names}
MONTH_RE = re.compile(r"\b(" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\b", re.I)
PLACE_RE = re.compile(r"\b(?:in|at|near|around)\s+([A-Za-zÁÉÍÓÚáéíóú'’\-]+(?:\s+[A-Z][A-Za-zÁÉÍÓÚáéíóú'’\-]+)?)")


def parse_question(text: str) -> ParsedQuestion:
    q = ParsedQuestion(text=text.strip())
    t = q.text
    low = t.lower()

    if re.fullmatch(r"\s*(help|\?|what can you do\??|hi|hello)\s*", low):
        q.is_help = True
        return q

    if re.search(r"\bcity\b", low) and not re.search(r"\bcounty\b", low):
        q.authority = CITY
    elif re.search(r"\bcounty\b", low):
        q.authority = COUNTY

    # References: explicit ("ref 2447", "application 268") always count; bare numbers
    # count when 5+ digits, or 3-4 digits that cannot be a year.
    refs = [m.group(1) for m in REF_CONTEXT_RE.finditer(t)]
    for m in NUMBER_RE.finditer(t):
        num = m.group(1)
        if num in refs:
            continue
        if len(num) >= 5 or (len(num) <= 4 and not YEAR_RE.fullmatch(num)):
            refs.append(num)
    q.refs = list(dict.fromkeys(refs))

    years = [int(y) for y in YEAR_RE.findall(t) if y not in q.refs]
    if years:
        q.year = years[0]

    if re.search(r"\brefus|\breject|\bturned down|\bdenied|\bwhy\b", low):
        q.decision = "REFUSED" if not re.search(r"\bcondition", low) else None
    if re.search(r"\bgrant|\bapprov|\bconditions?\b|\bpermitted\b", low) and not re.search(r"\brefus|\breject", low):
        q.decision = "CONDITIONAL"
    q.wants_reasons = bool(re.search(r"\bwhy\b|\breasons?\b|\brefus|\breject", low))
    q.wants_conditions = bool(re.search(r"\bconditions?\b", low))
    q.wants_count = bool(re.search(r"\bhow many\b|\bnumber of\b|\bcount\b|\btotal\b", low))

    q.asks_item_text = bool(re.search(r"\bwhy\b|\breasons?\b|\bconditions?\b", low))

    for m in MONTH_RE.finditer(t):
        word = m.group(1)
        if word.lower() == "may":
            # "may" is usually a verb: accept "May" capitalised, "in/of/during may", or "may 2026"
            before, after = t[:m.start()].lower().rstrip(), t[m.end():]
            if not (word == "May" or re.search(r"\b(in|of|during|since)$", before) or re.match(r"\s+20\d\d", after)):
                continue
        q.month = MONTHS[word.lower()]
        break

    for m in PLACE_RE.finditer(t):
        place = m.group(1).strip(" '’-")
        first = place.split()[0].lower() if place else ""
        if (place.lower() in STOPWORDS or first in MONTHS or first in STOPWORDS
                or YEAR_RE.fullmatch(place) or place.isdigit()):
            continue
        q.place = place
        break

    words = re.findall(r"[a-zA-Z][a-zA-Z\-]+", low)
    place_words = set((q.place or "").lower().split())
    for w in words:
        if w in STOPWORDS or w in place_words or len(w) < 3 or w in q.topic_terms:
            continue
        q.topic_terms.append(w)
        q.topic_groups.append(TOPIC_SYNONYMS.get(w, [w]))
    return q
