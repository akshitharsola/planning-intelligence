from src.sources.galway.city.scraper import GalwayCityScraper


def test_normalise_week_handles_dot_date_ranges():
    assert GalwayCityScraper._normalise_week("02.03.2026-06.03.2026") == "2-6"
    assert GalwayCityScraper._normalise_week("02.02.2026 - 06.02.2026") == "2-6"
    assert GalwayCityScraper._normalise_week("05.01.2026 to 09.01.2026") == "5-9"
    assert GalwayCityScraper._normalise_week("2-6") == "2-6"


def test_build_local_path_uses_temp_dir(tmp_path):
    config = {"pdf_patterns": {}, "base_url": "https://files.galwaycity.ie/gccplanninglists/"}
    scraper = GalwayCityScraper(region_config=config, temp_dir=tmp_path)
    link = {
        "filename": "Weekly Lists - Planning Applications Received.pdf",
        "year": 2026,
        "month_name": "March",
        "week_range": "2-6",
    }
    path = scraper._build_local_path(link)
    assert path == tmp_path / "2026" / "March" / "2-6" / link["filename"]
