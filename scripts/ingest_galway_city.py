"""
Galway City ingestion CLI: discover -> acquire -> parse -> normalize ->
resolve -> publish against the live filegator PDF source, using
per-file ingestion tracking so re-runs skip already-processed PDFs. A
file is only marked ingested once every row in it succeeds (self-healing
retry on partial failure). See
docs/superpowers/specs/2026-06-30-ingestion-cli-design.md section 4.
"""

import argparse
import logging
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
    """Re-derive which pdf_patterns key matched this filename.

    GalwayCityScraper.discover() already filters to filenames containing a
    known substring from config/galway/city.yaml's pdf_patterns, but does
    not report which key matched. Mirrors the scraper's own matching at
    src/sources/galway/city/scraper.py:67 (lowercased filename, literal
    space-separated substrings).
    """
    pdf_patterns = region_config["pdf_patterns"]
    lower = filename.lower()
    for source_type, substrings in pdf_patterns.items():
        if any(s in lower for s in substrings):
            return source_type
    return None


def run_city_ingestion(dry_run: bool = False) -> dict:
    session = SessionLocal()
    try:
        region_config = load_region_config(CONFIG_PATH)
        scraper = GalwayCityScraper(region_config=region_config, temp_dir=Path("data/galway/city/raw"))

        links = scraper.discover()
        skipped = 0
        to_acquire = []
        for link in links:
            if is_file_ingested(session, REGION, link["filename"]):
                skipped += 1
            else:
                to_acquire.append(link)

        ingested = 0
        failed = 0
        rejected = 0

        if to_acquire:
            local_paths = scraper.acquire(to_acquire)
            for local_path in local_paths:
                source_type = _match_source_type(local_path.name, region_config)
                if source_type is None:
                    logger.warning(
                        "Could not determine source_type for file=%s; skipping.",
                        local_path.name,
                    )
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
                            logger.warning(
                                "Rejected implausible row (not a real application) "
                                "region=%s file=%s file_number=%r applicant=%r: "
                                "file may be a non-application list mismatched by "
                                "pdf_patterns; check config/galway/city.yaml",
                                REGION, local_path.name, row.get("file_number"),
                                row.get("applicant"),
                            )
                            continue
                        if not dry_run:
                            resolve_and_upsert(session, app_create)
                        ingested += 1
                    except Exception as exc:
                        failed += 1
                        file_failed += 1
                        logger.error(
                            "Failed to ingest City row region=%s file=%s row=%s: %s",
                            REGION, local_path.name, row.get("file_number"), exc,
                        )

                if not dry_run and file_failed == 0:
                    mark_file_ingested(session, REGION, local_path.name)

        if not dry_run:
            publish(session, region=REGION, rows_ingested=ingested, parse_errors=failed)
            session.commit()

        logger.info(
            "City ingestion run complete: discovered=%d skipped_already_ingested=%d "
            "ingested=%d rejected=%d failed=%d dry_run=%s",
            len(links), skipped, ingested, rejected, failed, dry_run,
        )

        return {
            "discovered": len(links),
            "skipped_already_ingested": skipped,
            "ingested": ingested,
            "rejected": rejected,
            "failed": failed,
        }
    finally:
        session.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Ingest Galway City planning applications.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = run_city_ingestion(dry_run=args.dry_run)
    print(result)


if __name__ == "__main__":
    main()
