"""
Chunked backfill runner for Galway City: processes the discovered PDF
backlog in small batches with a pause between each, instead of hitting
the council file server ~1,200 times in one burst. Safe to re-run —
already-ingested files are skipped via is_file_ingested (same guarantee
as scripts/ingest_galway_city.py).

Usage: uv run python scripts/backfill_galway_city_chunked.py [--batch-size 50] [--pause-seconds 15] [--max-batches N]
"""

import argparse
import logging
import time
from pathlib import Path

from src.core.db.session import SessionLocal
from src.core.ingestion_state import is_file_ingested, mark_file_ingested
from src.parsers.pdf_lines.galway_city import extract_planning_table
from src.pipelines.discover import load_region_config
from src.pipelines.normalize import is_plausible_application_row, normalize_row
from src.pipelines.publish import publish
from src.pipelines.resolve import resolve_and_upsert
from src.sources.galway.city.scraper import GalwayCityScraper

logger = logging.getLogger(__name__)

REGION = "galway_city"
CONFIG_PATH = Path("config/galway/city.yaml")


def _match_source_type(filename: str, region_config: dict) -> str | None:
    pdf_patterns = region_config["pdf_patterns"]
    lower = filename.lower()
    for source_type, substrings in pdf_patterns.items():
        if any(s in lower for s in substrings):
            return source_type
    return None


def run_batch(scraper, region_config, session, batch_links) -> dict:
    ingested = failed = rejected = 0
    local_paths = scraper.acquire(batch_links)
    for local_path in local_paths:
        source_type = _match_source_type(local_path.name, region_config)
        if source_type is None:
            logger.warning("Could not determine source_type for file=%s; skipping.", local_path.name)
            continue

        rows = extract_planning_table(local_path, region_config["column_map"])
        file_failed = 0
        for row in rows:
            try:
                app_create = normalize_row(
                    row,
                    source_type=source_type,
                    region_config=region_config,
                    source_file=local_path.name,
                )
                if not is_plausible_application_row(app_create):
                    rejected += 1
                    continue
                resolve_and_upsert(session, app_create)
                ingested += 1
            except Exception:
                file_failed += 1
                failed += 1
                logger.exception(
                    "Failed to ingest City row region=%s file=%s row=%s",
                    REGION, local_path.name, row.get("file_number"),
                )

        if file_failed == 0:
            mark_file_ingested(session, REGION, local_path.name)

    publish(session, region=REGION, rows_ingested=ingested, parse_errors=failed)
    session.commit()
    return {"ingested": ingested, "rejected": rejected, "failed": failed}


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Chunked backfill for Galway City planning applications.")
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--pause-seconds", type=int, default=15)
    parser.add_argument("--max-batches", type=int, default=None, help="Stop after this many batches (for a first small test run).")
    args = parser.parse_args()

    session = SessionLocal()
    try:
        region_config = load_region_config(CONFIG_PATH)
        scraper = GalwayCityScraper(region_config=region_config, temp_dir=Path("data/galway/city/raw"))

        links = scraper.discover()
        to_acquire = [link for link in links if not is_file_ingested(session, REGION, link["filename"])]
        logger.info("Discovered=%d already_ingested=%d remaining=%d", len(links), len(links) - len(to_acquire), len(to_acquire))

        batches = [to_acquire[i:i + args.batch_size] for i in range(0, len(to_acquire), args.batch_size)]
        if args.max_batches:
            batches = batches[: args.max_batches]

        totals = {"ingested": 0, "rejected": 0, "failed": 0}
        for i, batch in enumerate(batches, 1):
            logger.info("=== Batch %d/%d (%d files) ===", i, len(batches), len(batch))
            result = run_batch(scraper, region_config, session, batch)
            for k in totals:
                totals[k] += result[k]
            logger.info("Batch %d result: %s | running totals: %s", i, result, totals)

            if i < len(batches):
                logger.info("Pausing %ds before next batch...", args.pause_seconds)
                time.sleep(args.pause_seconds)

        logger.info("Backfill run complete. Totals: %s", totals)
        print(totals)
    finally:
        session.close()


if __name__ == "__main__":
    main()
