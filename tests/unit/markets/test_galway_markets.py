from src.markets.registry import derive_market_entities


class FakeApplication:
    def __init__(self, planning_authority: str):
        self.planning_authority = planning_authority


def test_galway_city_council_maps_to_galway_city():
    app = FakeApplication("Galway City Council")
    assert derive_market_entities(app) == ["GALWAY_CITY"]


def test_galway_county_council_maps_to_galway_county():
    app = FakeApplication("Galway County Council")
    assert derive_market_entities(app) == ["GALWAY_COUNTY"]


def test_unknown_authority_maps_to_empty_list():
    app = FakeApplication("Some Other Council")
    assert derive_market_entities(app) == []
