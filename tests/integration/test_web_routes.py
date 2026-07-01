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
