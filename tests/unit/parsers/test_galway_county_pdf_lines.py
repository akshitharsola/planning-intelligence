from src.parsers.pdf_lines.galway_county import extract_from_rows

COUNTY_COLUMN_MAP = {
    "file number": "file_number",
    "applicants name": "applicant",
    "app. type": "app_type",
    "date received": "date_received",
    "development description and location": "description",
}


def test_extract_from_rows_maps_county_columns():
    raw_rows = [
        ["File Number", "Applicants Name", "App. Type", "Date Received",
         "Development Description and Location"],
        ["26/9999", "Mary Byrne", "P", "03/03/2026",
         "New dwelling at Oranmore Co. Galway"],
    ]
    records = extract_from_rows(raw_rows, COUNTY_COLUMN_MAP)
    assert len(records) == 1
    assert records[0]["file_number"] == "26/9999"
    assert records[0]["applicant"] == "Mary Byrne"
