"""
DHLGH enrichment backfill (spec
docs/superpowers/specs/2026-07-28-dhlgh-enrichment-backfill-design.md).
Backfills applications.site_address / site_geometry from
dhlgh_applications wherever the matching ladder (src/core/matching/ladder.py)
finds a unique rung-1 or rung-2 match and our own field is currently NULL.

build_enrichment_plan performs no writes. apply_enrichment_plan performs
the writes and must only be called after reviewing the plan (see --apply
flag below).
"""

import argparse
import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.core.db.session import SessionLocal
from src.core.matching.ladder import MatchCandidate, run_ladder
from src.core.models.application import Application
from src.core.models.dhlgh_application import DHLGHApplication

logger = logging.getLogger(__name__)

AUTHORITIES = ["Galway City Council", "Galway County Council"]


def build_enrichment_plan(
    session: Session, authority_filter: str | None = None, ref_prefix: str | None = None
) -> list[dict]:
    authorities = [authority_filter] if authority_filter else AUTHORITIES

    plan: list[dict] = []

    for authority in authorities:
        app_query = select(Application).where(Application.planning_authority == authority)
        dhlgh_query = select(DHLGHApplication).where(DHLGHApplication.planning_authority == authority)
        if ref_prefix:
            app_query = app_query.where(Application.application_ref.like(f"{ref_prefix}%"))
            dhlgh_query = dhlgh_query.where(DHLGHApplication.application_ref.like(f"{ref_prefix}%"))

        our_rows = session.scalars(app_query).all()
        dhlgh_rows = session.scalars(dhlgh_query).all()

        candidates = [
            MatchCandidate(
                application_ref=row.application_ref,
                site_address=row.site_address,
                site_geometry_wkt=None,
                application_id=row.id,
            )
            for row in our_rows
        ]
        by_id = {row.id: row for row in our_rows}

        for dhlgh_row in dhlgh_rows:
            geom_wkt = (
                session.scalar(select(func.ST_AsText(dhlgh_row.site_geometry)))
                if dhlgh_row.site_geometry is not None
                else None
            )
            result = run_ladder(
                session,
                dhlgh_ref=dhlgh_row.application_ref,
                dhlgh_address=dhlgh_row.site_address,
                dhlgh_geom_wkt=geom_wkt,
                authority=authority,
                candidates=candidates,
            )

            if not result.matched or result.rung not in (1, 2):
                continue

            matched_candidate = _find_matched_candidate(result.rung, dhlgh_row, candidates)
            if matched_candidate is None:
                continue

            app_row = by_id[matched_candidate.application_id]

            if app_row.site_address is None and dhlgh_row.site_address:
                plan.append({
                    "application_id": app_row.id,
                    "application_ref": app_row.application_ref,
                    "field": "site_address",
                    "new_value": dhlgh_row.site_address,
                    "source_dhlgh_ref": dhlgh_row.application_ref,
                    "rung": result.rung,
                })

            if app_row.site_geometry is None and dhlgh_row.site_geometry is not None:
                dhlgh_geom_wkt = session.scalar(select(func.ST_AsText(dhlgh_row.site_geometry)))
                plan.append({
                    "application_id": app_row.id,
                    "application_ref": app_row.application_ref,
                    "field": "site_geometry",
                    "new_value": dhlgh_geom_wkt,
                    "source_dhlgh_ref": dhlgh_row.application_ref,
                    "rung": result.rung,
                })

    return _drop_conflicting_targets(plan)


def _drop_conflicting_targets(plan: list[dict]) -> list[dict]:
    """Distinct DHLGH rows can each independently resolve to the same
    applications row/field (e.g. several DHLGH records sharing a
    duplicate address). Applying more than one such write would let list
    order silently pick a winner, so any (application_id, field) target
    that appears more than once in the plan is dropped entirely rather
    than guessing which source is correct."""
    counts: dict[tuple[uuid.UUID, str], int] = {}
    for item in plan:
        key = (item["application_id"], item["field"])
        counts[key] = counts.get(key, 0) + 1

    conflicts = {key for key, count in counts.items() if count > 1}
    if conflicts:
        logger.warning(
            "Dropping %d planned update(s) across %d (application_id, field) targets with conflicting DHLGH sources",
            sum(counts[key] for key in conflicts),
            len(conflicts),
        )

    return [item for item in plan if (item["application_id"], item["field"]) not in conflicts]


def _find_matched_candidate(rung: int, dhlgh_row, candidates: list[MatchCandidate]) -> MatchCandidate | None:
    """Re-applies the same equality predicate the winning rung used, to
    recover which candidate it was (run_ladder's MatchResult only reports
    matched/rung/ambiguous, not candidate identity)."""
    if rung == 1:
        from src.core.normalization.application_ref import normalize_application_ref
        normalized = normalize_application_ref(dhlgh_row.application_ref, dhlgh_row.planning_authority)
        target = normalized if normalized is not None else dhlgh_row.application_ref
        hits = [c for c in candidates if c.application_ref == target]
    elif rung == 2:
        from src.core.normalization.address import normalize_address
        target = normalize_address(dhlgh_row.site_address)
        hits = [
            c for c in candidates
            if c.site_address and normalize_address(c.site_address) == target
        ]
    else:
        return None

    return hits[0] if len(hits) == 1 else None


def apply_enrichment_plan(session: Session, plan: list[dict]) -> int:
    updated = 0
    for item in plan:
        app_row = session.get(Application, item["application_id"])
        if app_row is None:
            logger.warning(
                "Skipping planned update for application_id=%s: row no longer exists",
                item["application_id"],
            )
            continue
        setattr(app_row, item["field"], item["new_value"])
        updated += 1
    session.commit()
    return updated


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Apply the plan (default is dry-run print only)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    session = SessionLocal()
    try:
        plan = build_enrichment_plan(session)
        by_field = {}
        by_rung = {}
        for item in plan:
            by_field[item["field"]] = by_field.get(item["field"], 0) + 1
            by_rung[item["rung"]] = by_rung.get(item["rung"], 0) + 1

        logger.info("Enrichment plan: %d planned updates. By field: %s. By rung: %s", len(plan), by_field, by_rung)
        for item in plan[:10]:
            print(item)

        if args.apply:
            updated = apply_enrichment_plan(session, plan)
            logger.info("Applied %d updates.", updated)
        else:
            logger.info("Dry-run only (no writes). Re-run with --apply to write these changes.")
    finally:
        session.close()
