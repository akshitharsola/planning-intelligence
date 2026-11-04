"""Ingestion pipeline for decision notices into decision_documents and decision_items."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
import hashlib
import logging
import random
import subprocess
from typing import Optional
from sqlalchemy.orm import Session

from src.core.models.decision_document import DecisionDocument
from src.core.models.decision_item import DecisionItem
from src.core.models.dhlgh_application import DHLGHApplication
from src.parsers.decision_notice.extractor import (
    get_stated_count,
    has_text_layer,
    parse_notice,
)
from src.sources.galway.decision_documents import CountyDocFetcher, DocLink, list_decision_docs

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    documents_stored: int = 0
    documents_skipped_unchanged: int = 0
    failures: int = 0
    statuses: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def merge(self, other: "IngestResult") -> None:
        self.documents_stored += other.documents_stored
        self.documents_skipped_unchanged += other.documents_skipped_unchanged
        self.failures += other.failures
        for status, count in other.statuses.items():
            self.statuses[status] += count


def extract_pdf_layout_text(pdf_bytes: bytes) -> tuple[str, int]:
    """Extract layout-preserved text from PDF bytes using pdftotext.

    Returns (extracted_text, page_count).
    """
    proc = subprocess.run(
        ["pdftotext", "-layout", "-", "-"],
        input=pdf_bytes,
        capture_output=True,
    )
    raw_text = proc.stdout.decode("utf-8", "replace") if proc.stdout else ""
    # Count page breaks (form feeds \x0c) to estimate page count
    pages = raw_text.split("\x0c")
    page_count = max(1, len([p for p in pages if p.strip()] or [1]))
    return raw_text, page_count


def ingest_application(
    session: Session,
    fetcher: CountyDocFetcher,
    application: DHLGHApplication,
    dry_run: bool = False,
) -> IngestResult:
    """Fetch and ingest all decision notices for an application.

    Idempotent: skips documents whose content_sha256 is unchanged.
    Stores items for validated, count_mismatch, and unverified documents.
    """
    result = IngestResult()

    try:
        html = fetcher.fetch_list(application.application_ref)
    except Exception as e:
        logger.error("Failed fetching doc list for %s: %s", application.application_ref, e)
        result.failures += 1
        return result

    if not html:
        return result

    links = list_decision_docs(html, application.application_ref)
    if not links:
        return result

    for link in links:
        try:
            pdf_bytes = fetcher.fetch_pdf(link)
        except Exception as e:
            logger.error(
                "Failed fetching PDF %s for ref %s: %s",
                link.council_doc_id,
                application.application_ref,
                e,
            )
            result.failures += 1
            continue

        if not pdf_bytes:
            logger.warning(
                "Document %s for ref %s returned no valid PDF bytes",
                link.council_doc_id,
                application.application_ref,
            )
            result.failures += 1
            continue

        content_sha256 = hashlib.sha256(pdf_bytes).hexdigest()

        # Check existing row
        existing_doc = (
            session.query(DecisionDocument)
            .filter_by(
                planning_authority=application.planning_authority,
                council_doc_id=link.council_doc_id,
            )
            .one_or_none()
        )

        if existing_doc and existing_doc.content_sha256 == content_sha256:
            result.documents_skipped_unchanged += 1
            result.statuses[existing_doc.status] += 1
            continue

        try:
            raw_text, page_count = extract_pdf_layout_text(pdf_bytes)
        except Exception as e:
            logger.error("Failed pdftotext extraction for doc %s: %s", link.council_doc_id, e)
            result.failures += 1
            continue

        if not has_text_layer(raw_text, authority=application.planning_authority):
            parsed = parse_notice(
                raw_text,
                authority=application.planning_authority,
                decision=application.decision,
            )
        else:
            stated = get_stated_count(raw_text)
            eplan_count = None
            if stated is None:
                try:
                    eplan_count = fetcher.fetch_eplanning_condition_count(application.application_ref)
                except Exception as e:
                    logger.warning("Failed fetching ePlanning count for %s: %s", application.application_ref, e)
            parsed = parse_notice(
                raw_text,
                authority=application.planning_authority,
                eplan_count=eplan_count,
                decision=application.decision,
            )

        if not dry_run:
            now = datetime.now()
            default_kind = "refusal_reason" if "REFU" in (application.decision or "").upper() else "condition"
            item_kind = parsed.kind or default_kind

            if existing_doc:
                existing_doc.doc_type = link.doc_type
                existing_doc.source_url = link.url
                existing_doc.content_sha256 = content_sha256
                existing_doc.page_count = page_count
                existing_doc.raw_text = raw_text
                existing_doc.status = parsed.status
                existing_doc.stated_count = parsed.stated_count
                existing_doc.target_count = parsed.target_count
                existing_doc.parsed_count = len(parsed.items)
                existing_doc.failure_reason = parsed.failure_reason
                existing_doc.extracted_at = now

                # Clear previous items and replace
                existing_doc.items.clear()
                session.flush()

                if parsed.status in ("validated", "count_mismatch", "unverified"):
                    for item in parsed.items:
                        db_item = DecisionItem(
                            document_id=existing_doc.id,
                            item_no=item.n,
                            kind=item_kind,
                            text=item.text,
                            reason_text=item.reason_text,
                        )
                        session.add(db_item)
                session.commit()
            else:
                new_doc = DecisionDocument(
                    planning_authority=application.planning_authority,
                    application_ref=application.application_ref,
                    dhlgh_application_id=application.id,
                    council_doc_id=link.council_doc_id,
                    doc_type=link.doc_type,
                    source_url=link.url,
                    content_sha256=content_sha256,
                    page_count=page_count,
                    extraction_method="pdftotext",
                    raw_text=raw_text,
                    parser_version="1",
                    status=parsed.status,
                    stated_count=parsed.stated_count,
                    target_count=parsed.target_count,
                    parsed_count=len(parsed.items),
                    failure_reason=parsed.failure_reason,
                    fetched_at=now,
                    extracted_at=now,
                )
                session.add(new_doc)
                session.flush()

                if parsed.status in ("validated", "count_mismatch", "unverified"):
                    for item in parsed.items:
                        db_item = DecisionItem(
                            document_id=new_doc.id,
                            item_no=item.n,
                            kind=item_kind,
                            text=item.text,
                            reason_text=item.reason_text,
                        )
                        session.add(db_item)
                session.commit()

        result.documents_stored += 1
        result.statuses[parsed.status] += 1

    return result


def ingest_authority(
    session: Session,
    fetcher: CountyDocFetcher,
    authority: str = "Galway County Council",
    from_date: Optional[date] = None,
    since_year: Optional[int] = None,
    limit: Optional[int] = None,
    refs: Optional[list[str]] = None,
    sample: Optional[int] = None,
    seed: Optional[int] = None,
    dry_run: bool = False,
) -> IngestResult:
    """Run decision document ingestion across eligible applications in an authority."""
    query = session.query(DHLGHApplication).filter(DHLGHApplication.planning_authority == authority)
    query = query.filter(DHLGHApplication.decision.in_(["CONDITIONAL", "REFUSED"]))

    if refs:
        query = query.filter(DHLGHApplication.application_ref.in_(refs))
    elif from_date:
        query = query.filter(DHLGHApplication.decision_date >= from_date)
    elif since_year:
        query = query.filter(DHLGHApplication.decision_date >= date(since_year, 1, 1))

    query = query.order_by(
        DHLGHApplication.decision_date.asc().nulls_last(),
        DHLGHApplication.application_ref.asc(),
    )

    applications = query.all()

    if sample is not None and len(applications) > sample:
        rng = random.Random(seed if seed is not None else 42)
        applications = rng.sample(applications, sample)
        applications = sorted(applications, key=lambda a: a.application_ref)
    elif sample is not None:
        applications = sorted(applications, key=lambda a: a.application_ref)
    elif limit is not None:
        applications = applications[:limit]

    total_result = IngestResult()
    action_label = "parsed" if dry_run else "stored"

    print(f"Ingesting decision documents for {len(applications)} applications (authority: {authority}, dry_run={dry_run})...")

    for idx, app in enumerate(applications, start=1):
        try:
            app_result = ingest_application(session, fetcher, app, dry_run=dry_run)
            total_result.merge(app_result)
            stored = app_result.documents_stored
            skipped = app_result.documents_skipped_unchanged
            stat_str = ", ".join(f"{k}={v}" for k, v in sorted(app_result.statuses.items())) if app_result.statuses else "none"
            print(f"[{idx}/{len(applications)}] {app.application_ref} ({app.decision}): {action_label}={stored}, skipped={skipped} [{stat_str}]")
        except RuntimeError as e:
            # Re-raise server aborts (e.g. repeated 429/403) immediately
            print(f"[{idx}/{len(applications)}] {app.application_ref}: CRITICAL ERROR - {e}")
            raise
        except Exception as e:
            logger.error("Unhandled error ingesting application %s: %s", app.application_ref, e)
            total_result.failures += 1
            print(f"[{idx}/{len(applications)}] {app.application_ref}: FAILED ({e})")

    print("\n--- Ingest Summary ---")
    print(f"Documents {action_label}:        {total_result.documents_stored}")
    print(f"Documents skipped unchanged: {total_result.documents_skipped_unchanged}")
    print(f"Application fetch failures:  {total_result.failures}")
    print("Status Histogram:")
    for status, count in sorted(total_result.statuses.items()):
        print(f"  {status:16}: {count}")

    return total_result
