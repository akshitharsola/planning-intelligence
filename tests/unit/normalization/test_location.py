from src.core.normalization.location import extract_location


def test_extract_location_finds_eircode_and_area():
    desc = "Construction of extension at 19 Monivea Road Mervue Galway H91 TX20"
    loc = extract_location(desc)
    assert loc["eircode"] == "H91 TX20"
    assert loc["area"] == "Mervue"


def test_extract_location_handles_empty_description():
    assert extract_location("") == {"area": "", "address": "", "eircode": ""}
