"""
DHLGH cross-source identity matching validation pass (spec section 9,
docs/superpowers/specs/2026-07-10-dhlgh-national-source-design.md). Runs
the matching ladder (src/core/matching/ladder.py) across the full Galway
overlap between `applications` and `dhlgh_applications` and reports
per-rung match counts, per-authority coverage, and dhlgh_applications
field-quality stats.

Read-only against `applications`: this pass never writes, merges, or
upserts. Its only output is the printed/returned report dict, for a
future separate decision on whether/how to act on DHLGH data.
"""

import argparse
import logging
from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.core.db.session import SessionLocal
from src.core.matching.ladder import MatchCandidate, run_ladder
from src.core.models.application import Application
from src.core.models.dhlgh_application import DHLGHApplication

logger = logging.getLogger(__name__)

AUTHORITIES = ["Galway City Council", "Galway County Council"]


def build_validation_report(
    session: Session, authority_filter: str | None = None, ref_prefix: str | None = None
) -> dict:
    authorities = [authority_filter] if authority_filter else AUTHORITIES

    by_rung = defaultdict(int)
    coverage = {}

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
            )
            for row in our_rows
        ]

        coverage[authority] = {"dhlgh_count": len(dhlgh_rows), "our_count": len(our_rows)}

        for row in dhlgh_rows:
            geom_wkt = session.scalar(select(func.ST_AsText(row.site_geometry))) if row.site_geometry is not None else None
            result = run_ladder(
                session,
                dhlgh_ref=row.application_ref,
                dhlgh_address=row.site_address,
                dhlgh_geom_wkt=geom_wkt,
                authority=authority,
                candidates=candidates,
            )
            if result.ambiguous:
                by_rung["ambiguous"] += 1
            elif result.matched and result.rung == 4:
                by_rung["rung_4_manual_review"] += 1
            elif result.matched:
                by_rung[f"rung_{result.rung}"] += 1
            else:
                by_rung["no_match"] += 1

    total_dhlgh_rows = sum(c["dhlgh_count"] for c in coverage.values())

    all_dhlgh = session.scalars(
        select(DHLGHApplication).where(DHLGHApplication.planning_authority.in_(authorities))
    ).all()
    non_null_address = sum(1 for r in all_dhlgh if r.site_address)
    non_null_geometry = sum(1 for r in all_dhlgh if r.site_geometry is not None)
    field_quality = {
        "dhlgh_site_address_non_null_pct": round(100 * non_null_address / len(all_dhlgh), 1) if all_dhlgh else 0.0,
        "dhlgh_site_geometry_non_null_pct": round(100 * non_null_geometry / len(all_dhlgh), 1) if all_dhlgh else 0.0,
    }

    return {
        "total_dhlgh_rows": total_dhlgh_rows,
        "by_rung": dict(by_rung),
        "coverage": coverage,
        "field_quality": field_quality,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    session = SessionLocal()
    try:
        report = build_validation_report(session)
        logger.info("Validation pass complete: %s", report)
        print(report)
    finally:
        session.close()
