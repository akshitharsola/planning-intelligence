"""
Cross-source identity matching ladder (spec section 9,
docs/superpowers/specs/2026-07-10-dhlgh-national-source-design.md). Given
a DHLGH row and the subset of our own `applications` rows sharing its
planning_authority, tries each rung in order and stops at the first rung
that finds a UNIQUE match. A rung returning more than one candidate is
ambiguous, not a match, and the caller falls through to the next rung.

This module does not touch the database or write to `applications` — it
operates on plain MatchCandidate values so it stays trivially unit
testable. Callers (the validation-pass CLI) are responsible for loading
candidates and persisting/reporting results.
"""

from typing import NamedTuple

from src.core.normalization.application_ref import normalize_application_ref


class MatchCandidate(NamedTuple):
    application_ref: str
    site_address: str | None
    site_geometry_wkt: str | None


class MatchResult(NamedTuple):
    matched: bool
    rung: int | None
    ambiguous: bool


def rung1_ref_match(
    dhlgh_ref: str, authority: str, candidates: list[MatchCandidate]
) -> MatchResult:
    normalized = normalize_application_ref(dhlgh_ref, authority)
    target = normalized if normalized is not None else dhlgh_ref

    hits = [c for c in candidates if c.application_ref == target]

    if len(hits) == 1:
        return MatchResult(matched=True, rung=1, ambiguous=False)
    if len(hits) > 1:
        return MatchResult(matched=False, rung=None, ambiguous=True)
    return MatchResult(matched=False, rung=None, ambiguous=False)
