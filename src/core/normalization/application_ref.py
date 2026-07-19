"""
normalize_application_ref() — cross-source identity matching ladder rung 1
helper (spec section 9.1,
docs/superpowers/specs/2026-07-10-dhlgh-national-source-design.md).

Not a one-line regex assumed correct: ref formats vary by authority, by
era within the same authority, and possibly by source (confirmed via live
data pulled from our own `applications` table and the DHLGH endpoint
during spec review — see the module docstring's fixture table below).
This is a small pure function — no network or DB access — so it is
trivially unit-testable in isolation.

Only one rule-based transform is currently demonstrated from real data:
City's `YY` + 5-digit sequence starting with `60` (e.g. "2660243") maps to
our own `YY/60NNN` shape (e.g. "26/60243"), confirmed against real City
refs "24/60030", "23/60030" already in our table. Every other observed
County shape (`26170`, `2661119`, `163`) has no demonstrated, reliable
transform — the caller must treat NORMALIZE_FAILED as "fall through to
rung 2 of the ladder", never as license to guess a rule that isn't
verified against real fixtures. Do not add a broader/looser rule to widen
rung 1's coverage without new confirmed fixtures — that reintroduces the
exact silent-merge risk (documented in spec section 9) this function
exists to prevent.
"""

import re

NORMALIZE_FAILED = None

# City 2026-era refs: 2-digit year + "60" + 3 more digits, no slash, 7
# digits total (e.g. "2660243" -> "26/60243"). Verified against
# real City application_ref values already in our own table using this
# exact "YY/60NNN" shape.
_CITY_YY_60NNN_RE = re.compile(r"^(\d{2})(60\d{3})$")

# Already-normalized City refs (e.g. "24/60030") pass through unchanged —
# confirms idempotency (spec section 9.1 fixture table, last row).
_ALREADY_NORMALIZED_RE = re.compile(r"^\d{2}/60\d{3}$")


def normalize_application_ref(application_number: str, authority: str) -> str | None:
    """Returns the normalized ref string, or None (NORMALIZE_FAILED) if no
    known rule applies to this input. A None return is not an error — the
    caller is required to log it and fall through to rung 2 of the
    matching ladder rather than guess."""
    value = (application_number or "").strip()
    if not value:
        return NORMALIZE_FAILED

    if _ALREADY_NORMALIZED_RE.match(value):
        return value

    match = _CITY_YY_60NNN_RE.match(value)
    if match:
        year, sequence = match.groups()
        return f"{year}/{sequence}"

    return NORMALIZE_FAILED
