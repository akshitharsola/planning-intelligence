from unittest.mock import MagicMock, patch

from src.sources.galway.county.scraper import GalwayCountyScraper

CONFIG = {
    "arcgis_query_url": "https://services1.arcgis.com/mJI7JYqAOKXPG7Hh/arcgis/rest/services/GCC_PlanningRegisterPts_16/FeatureServer/2/query",
    "watermark_field": "OBJECTID",
    "page_size": 2,
    "out_fields": ["OBJECTID", "ApplicationNumber"],
}


def _response(features):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"features": [{"attributes": a} for a in features]}
    return resp


def test_discover_paginates_until_short_page():
    page1 = _response([{"OBJECTID": 1, "ApplicationNumber": "A"}, {"OBJECTID": 2, "ApplicationNumber": "B"}])
    page2 = _response([{"OBJECTID": 3, "ApplicationNumber": "C"}])

    with patch("requests.Session.get", side_effect=[page1, page2]):
        scraper = GalwayCountyScraper(region_config=CONFIG, temp_dir="/tmp/unused")
        records = scraper.discover()

    assert [r["OBJECTID"] for r in records] == [1, 2, 3]


def test_discover_stops_on_empty_page():
    with patch("requests.Session.get", return_value=_response([])):
        scraper = GalwayCountyScraper(region_config=CONFIG, temp_dir="/tmp/unused")
        assert scraper.discover() == []


def test_acquire_is_passthrough():
    scraper = GalwayCountyScraper(region_config=CONFIG, temp_dir="/tmp/unused")
    items = [{"OBJECTID": 1}]
    assert scraper.acquire(items) is items
