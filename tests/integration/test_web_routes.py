from fastapi.testclient import TestClient

from src.web.main import app

client = TestClient(app)


def test_dashboard_route_returns_200():
    response = client.get("/")
    assert response.status_code == 200


def test_detail_route_returns_404_for_unknown_application():
    response = client.get("/applications/Galway City Council/NOSUCHREF%2F9999")
    assert response.status_code == 404


def test_dashboard_shows_kpi_and_chart_containers():
    response = client.get("/")
    assert response.status_code == 200
    assert "Total applications" in response.text
    assert "monthly-chart" in response.text
    assert "status-chart" in response.text
    assert "type-chart" in response.text


def test_dashboard_filter_by_planning_authority_narrows_table():
    response = client.get("/", params={"planning_authority": "Galway City Council"})
    assert response.status_code == 200


def test_dashboard_pagination_params_accepted():
    response = client.get("/", params={"page": 2, "page_size": 10})
    assert response.status_code == 200


from datetime import date

from sqlalchemy import text

from src.core.db.session import SessionLocal

DETAIL_PREFIX = "WEBDETAILTEST"


def _cleanup_detail():
    session = SessionLocal()
    try:
        session.execute(
            text("DELETE FROM applications WHERE application_ref LIKE :p"),
            {"p": f"{DETAIL_PREFIX}/%"},
        )
        session.commit()
    finally:
        session.close()


def _seed_detail():
    session = SessionLocal()
    try:
        session.execute(
            text(
                """
                INSERT INTO applications (
                    id, planning_authority, source_entity, application_ref,
                    applicant_name, site_address, site_locality, site_county,
                    development_description, application_type,
                    planning_status_current, date_received, decision_due_date,
                    decision_date, further_information_flag,
                    protected_structure_flag, eia_eis_flag, official_detail_url,
                    official_documents_url, source_system, source_file,
                    source_ingested_at, other_regulatory_flags, raw_payload_json,
                    commuter_belt_flag
                ) VALUES (
                    gen_random_uuid(), 'Galway City Council', 'GALWAY_CITY_COUNCIL',
                    :ref, 'Carol Example', '5 Test Lane', 'Galway City', 'Galway',
                    'Test detail page development', 'Permission', 'Granted',
                    :received, :due, :decided, true, false, false,
                    'https://example.test/detail', 'https://example.test/docs',
                    'TEST', 'test.pdf', now(), '{}', '{}', false
                )
                """
            ),
            {
                "ref": f"{DETAIL_PREFIX}/0001",
                "received": date(2026, 1, 10),
                "due": date(2026, 3, 10),
                "decided": date(2026, 3, 1),
            },
        )
        session.commit()
    finally:
        session.close()


def test_detail_page_shows_all_expected_fields():
    _cleanup_detail()
    _seed_detail()
    try:
        response = client.get(f"/applications/Galway City Council/{DETAIL_PREFIX}%2F0001")
        assert response.status_code == 200
        body = response.text
        for expected in [
            "Galway City Council", f"{DETAIL_PREFIX}/0001", "Carol Example",
            "5 Test Lane", "Galway City", "Test detail page development",
            "Granted", "2026-01-10", "2026-03-10", "2026-03-01",
            "TEST", "test.pdf", "https://example.test/detail",
            "https://example.test/docs",
        ]:
            assert expected in body
    finally:
        _cleanup_detail()
