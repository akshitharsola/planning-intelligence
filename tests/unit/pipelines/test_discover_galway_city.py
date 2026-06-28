from pathlib import Path

from src.pipelines.discover import load_region_config


def test_load_galway_city_config():
    config = load_region_config(Path("config/galway/city.yaml"))
    assert config["source_entity"] == "GALWAY_CITY_COUNCIL"
    assert config["planning_authority"] == "Galway City Council"
    assert "pdf_patterns" in config
    assert config["pdf_patterns"]["received"] == [
        "planning applications received",
        "received  applications",
        "received applications",
    ]
