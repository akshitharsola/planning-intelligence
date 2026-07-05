from datetime import date, datetime

from sqlalchemy import text

from src.core.db.session import SessionLocal
from src.services.dashboard_service import (
    get_summary,
    get_monthly_counts,
    get_status_breakdown,
    get_type_breakdown,
)

PREFIX = "DASHTEST"


def _cleanup():
    session = SessionLocal()
    try:
        session.execute(
            text("DELETE FROM application_events WHERE application_ref LIKE :p"),
            {"p": f"{PREFIX}/%"},
        )
        session.execute(
            text("DELETE FROM applications WHERE application_ref LIKE :p"),
            {"p": f"{PREFIX}/%"},
        )
        session.commit()
    finally:
        session.close()


def _insert_application(session, ref, authority, status, app_type, received, ingested_at):
    session.execute(
        text(
            """
            INSERT INTO applications (
                id, planning_authority, source_entity, application_ref,
                applicant_name, development_description, application_type,
                planning_status_current, date_received, source_system,
                source_file, source_ingested_at,
                further_information_flag, protected_structure_flag,
                eia_eis_flag, other_regulatory_flags, commuter_belt_flag,
                raw_payload_json
            ) VALUES (
                gen_random_uuid(), :authority, :authority, :ref,
                'Test Applicant', 'Test development', :app_type,
                :status, :received, 'TEST', 'test.pdf', :ingested_at,
                false, false, false, '{}', false, '{}'
            )
            """
        ),
        {
            "authority": authority,
            "ref": ref,
            "app_type": app_type,
            "status": status,
            "received": received,
            "ingested_at": ingested_at,
        },
    )


def _seed():
    session = SessionLocal()
    try:
        _insert_application(
            session, f"{PREFIX}/0001", "Galway City Council", "Granted", "Permission",
            date(2026, 1, 15), datetime(2026, 1, 16, 9, 0),
        )
        _insert_application(
            session, f"{PREFIX}/0002", "Galway City Council", "Granted", "Permission",
            date(2026, 1, 20), datetime(2026, 1, 21, 9, 0),
        )
        _insert_application(
            session, f"{PREFIX}/0003", "Galway County Council", "Refused", "RETENTION",
            date(2026, 2, 5), datetime(2026, 2, 6, 9, 0),
        )
        session.commit()
    finally:
        session.close()


def test_get_summary_counts_and_ranges():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            summary = get_summary(session)
        finally:
            session.close()
        assert summary["total_applications"] >= 3
        assert summary["distinct_authorities"] >= 2
        assert summary["earliest_received"] <= date(2026, 1, 15)
        assert summary["latest_received"] >= date(2026, 2, 5)
        assert summary["latest_ingested_at"] >= datetime(2026, 2, 6, 9, 0)
    finally:
        _cleanup()


def test_get_monthly_counts_groups_by_year_month():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            counts = get_monthly_counts(session)
        finally:
            session.close()
        by_label = {row["label"]: row["value"] for row in counts}
        assert by_label.get("2026-01", 0) >= 2
        assert by_label.get("2026-02", 0) >= 1
    finally:
        _cleanup()


def test_get_status_breakdown_groups_by_status():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            breakdown = get_status_breakdown(session)
        finally:
            session.close()
        by_label = {row["label"]: row["value"] for row in breakdown}
        assert by_label.get("Granted", 0) >= 2
        assert by_label.get("Refused", 0) >= 1
    finally:
        _cleanup()


def test_get_type_breakdown_groups_by_application_type():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            breakdown = get_type_breakdown(session)
        finally:
            session.close()
        by_label = {row["label"]: row["value"] for row in breakdown}
        assert by_label.get("Permission", 0) >= 2
        assert by_label.get("RETENTION", 0) >= 1
    finally:
        _cleanup()
