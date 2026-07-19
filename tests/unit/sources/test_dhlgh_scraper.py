from unittest.mock import MagicMock, patch

from src.sources.dhlgh.scraper import DHLGHScraper

CONFIG = {
    "arcgis_query_url": "https://services.arcgis.com/NzlPQPKn5QF9v2US/arcgis/rest/services/IrishPlanningApplications/FeatureServer/1/query",
    "watermark_field": "OBJECTID",
    "page_size": 2,
    "out_fields": ["OBJECTID", "ApplicationNumber"],
    "planning_authorities": ["Galway City Council", "Galway County Council"],
    "returnGeometry": True,
}


def _response(features):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"features": features}
    return resp


def test_discover_paginates_until_short_page():
    page1 = _response([
        {"attributes": {"OBJECTID": 1, "ApplicationNumber": "A"}},
        {"attributes": {"OBJECTID": 2, "ApplicationNumber": "B"}},
    ])
    page2 = _response([{"attributes": {"OBJECTID": 3, "ApplicationNumber": "C"}}])

    with patch("requests.Session.get", side_effect=[page1, page2]):
        scraper = DHLGHScraper(region_config=CONFIG, temp_dir="/tmp/unused")
        records = scraper.discover()

    assert [r["OBJECTID"] for r in records] == [1, 2, 3]


def test_discover_stops_on_empty_page():
    with patch("requests.Session.get", return_value=_response([])):
        scraper = DHLGHScraper(region_config=CONFIG, temp_dir="/tmp/unused")
        assert scraper.discover() == []


def test_discover_includes_planning_authority_filter_in_where_clause():
    captured = {}

    def fake_get(url, params, timeout):
        captured["where"] = params["where"]
        return _response([])

    with patch("requests.Session.get", side_effect=fake_get):
        scraper = DHLGHScraper(region_config=CONFIG, temp_dir="/tmp/unused")
        scraper.discover()

    assert "PlanningAuthority IN ('Galway City Council', 'Galway County Council')" in captured["where"]


def test_discover_geometry_is_attached_when_present():
    page = _response([
        {
            "attributes": {"OBJECTID": 1, "ApplicationNumber": "A"},
            "geometry": {"rings": [[[-9.0, 53.0], [-9.1, 53.1], [-9.2, 53.0]]]},
        }
    ])

    with patch("requests.Session.get", return_value=page):
        scraper = DHLGHScraper(region_config=CONFIG, temp_dir="/tmp/unused")
        records = scraper.discover()

    assert records[0]["_geometry"] == {"rings": [[[-9.0, 53.0], [-9.1, 53.1], [-9.2, 53.0]]]}


def test_acquire_is_passthrough():
    scraper = DHLGHScraper(region_config=CONFIG, temp_dir="/tmp/unused")
    items = [{"OBJECTID": 1}]
    assert scraper.acquire(items) is items
