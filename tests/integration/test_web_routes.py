from fastapi.testclient import TestClient

from src.web.main import app

client = TestClient(app)


def test_dashboard_route_returns_200():
    response = client.get("/")
    assert response.status_code == 200


def test_detail_route_returns_404_for_unknown_application():
    response = client.get("/applications/Galway City Council/NOSUCHREF%2F9999")
    assert response.status_code == 404
