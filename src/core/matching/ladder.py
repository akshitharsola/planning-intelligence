"""
Cross-source identity matching ladder (spec section 9,
docs/superpowers/specs/2026-07-10-dhlgh-national-source-design.md). Given
a DHLGH row and the subset of our own `applications` rows sharing its
planning_authority, tries each rung in order and stops at the first rung
that finds a UNIQUE match. A rung returning more than one candidate is
ambiguous, not a match, and the caller falls through to the next rung.

Rungs 1 and 2 do not touch the database or write to `applications` — they
operate on plain MatchCandidate values so they stay trivially unit
testable. Callers (the validation-pass CLI) are responsible for loading
candidates and persisting/reporting results.

Rung 3 (geometry proximity) is the exception: it queries the DB directly
via a SQLAlchemy `Session` rather than taking pre-loaded candidates,
because PostGIS distance computation is far cheaper done in SQL (using
spatial functions) than by pulling every geometry into Python and
computing distances there. This asymmetry versus rungs 1-2 is
intentional.
"""

from typing import NamedTuple

from geoalchemy2.functions import ST_DWithin, ST_GeogFromText
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.models.application import Application
from src.core.normalization.address import normalize_address
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


def rung2_address_match(
    dhlgh_address: str | None, candidates: list[MatchCandidate]
) -> MatchResult:
    if not dhlgh_address:
        return MatchResult(matched=False, rung=None, ambiguous=False)

    target = normalize_address(dhlgh_address)

    hits = [
        c for c in candidates
        if c.site_address and normalize_address(c.site_address) == target
    ]

    if len(hits) == 1:
        return MatchResult(matched=True, rung=2, ambiguous=False)
    if len(hits) > 1:
        return MatchResult(matched=False, rung=None, ambiguous=True)
    return MatchResult(matched=False, rung=None, ambiguous=False)


def rung3_geometry_match(
    session: Session,
    dhlgh_geom_wkt: str | None,
    authority: str,
    proximity_meters: float = 25.0,
) -> MatchResult:
    if not dhlgh_geom_wkt:
        return MatchResult(matched=False, rung=None, ambiguous=False)

    hits = session.scalars(
        select(Application.id).where(
            Application.planning_authority == authority,
            Application.site_geometry.isnot(None),
            ST_DWithin(
                ST_GeogFromText(Application.site_geometry.ST_AsText()),
                ST_GeogFromText(dhlgh_geom_wkt),
                proximity_meters,
            ),
        )
    ).all()

    if len(hits) == 1:
        return MatchResult(matched=True, rung=3, ambiguous=False)
    if len(hits) > 1:
        return MatchResult(matched=False, rung=None, ambiguous=True)
    return MatchResult(matched=False, rung=None, ambiguous=False)
