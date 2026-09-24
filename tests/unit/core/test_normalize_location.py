import pytest

from src.core.normalization.location import extract_eircode


@pytest.mark.parametrize(
    "text,expected",
    [
        ("...Threadneedle Road Galway H91WE0R", "H91WE0R"),
        ("...Threadneedle Road Galway H91 WE0R", "H91WE0R"),
        ("...Salthill Galway h91we0r", "H91WE0R"),  # lowercase input
        ("EOD on 17/133 ... H91 1X08", "H91 1X08".replace(" ", "")),
        ("No eircode in this description at all", ""),
        ("", ""),
        ("H91 xyz is incomplete", ""),  # only 3 chars after H91, not 4
        ("Partial H9WE0R is not valid (only one digit)", ""),
    ],
)
def test_extract_eircode(text, expected):
    assert extract_eircode(text) == expected


def test_extract_eircode_from_county_style_location_field():
    # County's Location field rarely has one, but when it does (9 of 20,805
    # live rows), it must still be found the same way as City's.
    assert extract_eircode("Shanbally, Craughwell, H91X3PN") == "H91X3PN"
