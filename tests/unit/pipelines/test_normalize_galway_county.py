from src.core.normalization.galway_county import normalize_county_row

REGION_CONFIG = {
    "source_entity": "GALWAY_COUNTY_COUNCIL",
    "planning_authority": "Galway County Council",
}


def test_normalize_county_row_received():
    raw_row = {
        "file_number": "26/9999",
        "applicant": "Mary Byrne",
        "app_type": "P",
        "date_received": "03/03/2026",
        "description": "New dwelling at Oranmore Co. Galway",
    }
    app = normalize_county_row(raw_row, source_type="received", region_config=REGION_CONFIG,
                               source_file="weekly-2026-03-02-received.pdf")
    assert app.application_ref == "26/9999"
    assert app.planning_authority == "Galway County Council"
    assert app.planning_status_current == "Received"
    assert app.site_county == "Galway"
