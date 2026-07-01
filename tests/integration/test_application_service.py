from datetime import date

from sqlalchemy import text

from src.core.db.session import SessionLocal
from src.services.application_service import search, get_by_natural_key

PREFIX = "APPSVCTEST"


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


def _insert(session, ref, authority, status, app_type, received, applicant, address, description):
    session.execute(
        text(
            """
            INSERT INTO applications (
                id, planning_authority, source_entity, application_ref,
                applicant_name, site_address, development_description,
                application_type, planning_status_current, date_received,
                source_system, source_file, source_ingested_at,
                further_information_flag, protected_structure_flag,
                eia_eis_flag, other_regulatory_flags, commuter_belt_flag,
                raw_payload_json
            ) VALUES (
                gen_random_uuid(), :authority, :authority, :ref,
                :applicant, :address, :description, :app_type, :status,
                :received, 'TEST', 'test.pdf', now(),
                false, false, false, '{}', false, '{}'
            )
            """
        ),
        {
            "authority": authority,
            "ref": ref,
            "applicant": applicant,
            "address": address,
            "description": description,
            "app_type": app_type,
            "status": status,
            "received": received,
        },
    )


def _seed():
    session = SessionLocal()
    try:
        _insert(
            session, f"{PREFIX}/0001", "Galway City Council", "Granted", "Permission",
            date(2026, 1, 15), "Alice Example", "1 Main Street, Galway",
            "New dwelling extension (APPSVCTEST)",
        )
        _insert(
            session, f"{PREFIX}/0002", "Galway County Council", "Refused", "RETENTION",
            date(2026, 2, 5), "Bob Sample", "2 Bridge Road, Oranmore",
            "Commercial signage installation (APPSVCTEST)",
        )
        session.commit()
    finally:
        session.close()


def test_get_by_natural_key_found():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            app = get_by_natural_key(session, "Galway City Council", f"{PREFIX}/0001")
        finally:
            session.close()
        assert app is not None
        assert app.applicant_name == "Alice Example"
    finally:
        _cleanup()


def test_get_by_natural_key_not_found_returns_none():
    session = SessionLocal()
    try:
        app = get_by_natural_key(session, "Galway City Council", "NOSUCHREF/9999")
    finally:
        session.close()
    assert app is None


def test_search_filters_by_planning_authority():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            rows, total = search(
                session,
                {"planning_authority": "Galway County Council", "q": PREFIX},
                page=1,
                page_size=25,
            )
        finally:
            session.close()
        refs = {r.application_ref for r in rows}
        assert f"{PREFIX}/0002" in refs
        assert f"{PREFIX}/0001" not in refs
        assert total == len(rows)
    finally:
        _cleanup()


def test_search_q_matches_site_address_case_insensitive():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            rows, total = search(session, {"q": "bridge road"}, page=1, page_size=25)
        finally:
            session.close()
        refs = {r.application_ref for r in rows}
        assert f"{PREFIX}/0002" in refs
        assert f"{PREFIX}/0001" not in refs
    finally:
        _cleanup()


def test_search_pagination_returns_correct_slice_and_total():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            rows_page1, total1 = search(
                session, {"q": PREFIX}, page=1, page_size=1
            )
            rows_page2, total2 = search(
                session, {"q": PREFIX}, page=2, page_size=1
            )
        finally:
            session.close()
        assert len(rows_page1) == 1
        assert len(rows_page2) == 1
        assert rows_page1[0].application_ref != rows_page2[0].application_ref
        assert total1 == total2 == 2
    finally:
        _cleanup()
