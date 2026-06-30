"""
Galway County ingestion CLI: discover -> normalize -> resolve -> publish
against the live ArcGIS Feature Service, using a persisted OBJECTID
watermark so re-runs only fetch new records. See
docs/superpowers/specs/2026-06-30-ingestion-cli-design.md section 3.
"""

import argparse
import logging
from pathlib import Path

from src.core.db.session import SessionLocal
from src.core.ingestion_state import get_watermark, set_watermark
from src.core.normalization.galway_county import normalize_county_row
from src.pipelines.discover import load_region_config
from src.pipelines.publish import publish
from src.pipelines.resolve import resolve_and_upsert
from src.sources.galway.county.scraper import GalwayCountyScraper

logger = logging.getLogger(__name__)

REGION = "galway_county"
CONFIG_PATH = Path("config/galway/county.yaml")


def run_county_ingestion(dry_run: bool = False) -> dict:
    session = SessionLocal()
    try:
        stored_watermark = get_watermark(session, REGION)
        region_config = load_region_config(CONFIG_PATH)
        region_config["watermark"] = int(stored_watermark) if stored_watermark else 0

        scraper = GalwayCountyScraper(region_config=region_config, temp_dir=Path("/tmp/unused"))
        records = scraper.discover()

        ingested = 0
        failed = 0
        max_success_objectid = None

        for record in records:
            object_id = record.get("OBJECTID")
            try:
                app_create = normalize_county_row(
                    record, region_config=region_config, source_file="arcgis_feature_service"
                )
                if not dry_run:
                    resolve_and_upsert(session, app_create)
                ingested += 1
                if max_success_objectid is None or object_id > max_success_objectid:
                    max_success_objectid = object_id
            except Exception as exc:
                failed += 1
                logger.error(
                    "Failed to ingest County record region=%s OBJECTID=%s: %s",
                    REGION, object_id, exc,
                )

        new_watermark = str(max_success_objectid) if max_success_objectid is not None else None

        if not dry_run:
            publish(session, region=REGION, rows_ingested=ingested, parse_errors=failed)
            if new_watermark is not None:
                set_watermark(session, REGION, new_watermark)
            session.commit()

        logger.info(
            "County ingestion run complete: discovered=%d ingested=%d failed=%d new_watermark=%s dry_run=%s",
            len(records), ingested, failed, new_watermark, dry_run,
        )

        return {
            "discovered": len(records),
            "ingested": ingested,
            "failed": failed,
            "new_watermark": new_watermark,
        }
    finally:
        session.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Ingest Galway County planning applications.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = run_county_ingestion(dry_run=args.dry_run)
    print(result)


if __name__ == "__main__":
    main()
