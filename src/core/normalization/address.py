"""
normalize_address() — cross-source identity matching ladder rung 2 helper
(spec section 9.2,
docs/superpowers/specs/2026-07-10-dhlgh-national-source-design.md). Fixed
recipe applied identically to both DevelopmentAddress (DHLGH) and
site_address (ours), so rung 2 is deterministic and reproducible.

Two normalized addresses match only if exactly equal after this recipe —
deliberately not fuzzy. Fuzzy comparison is reserved for rung 4 (trigram
similarity), so the two rungs have distinct, understood precision/recall
trade-offs.
"""

import re

# Built from real observed variants in the Galway address strings
# collected during spec review (section 9.2 step 4): "Co. Galway",
# "Co Galway", "County Galway" all appear as variants of the same thing.
_ABBREVIATION_MAP = {
    "co.": "county",
    "co": "county",
    "rd": "road",
    "st": "street",
}

_TRAILING_GALWAY_RE = re.compile(r"(?:\s+county\s+galway|\s+galway)$")


def normalize_address(address: str) -> str:
    value = (address or "").lower()

    # Strip punctuation except internal hyphens (keep "cul-de-sac"-style
    # names intact; drop commas, periods, apostrophes elsewhere).
    value = re.sub(r"[.,']", " ", value)
    value = re.sub(r"[^a-z0-9\s-]", " ", value)

    value = re.sub(r"\s+", " ", value).strip()

    tokens = [_ABBREVIATION_MAP.get(tok, tok) for tok in value.split(" ")]
    value = " ".join(tokens)

    # Drop trailing standalone "galway" / "county galway" tokens if the
    # rest of the string is non-empty — both sources redundantly append
    # the county name to nearly every address.
    stripped = _TRAILING_GALWAY_RE.sub("", value)
    if stripped.strip():
        value = stripped.strip()

    return value
