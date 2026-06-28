from src.parsers.pdf_lines.galway_city import _map_column, _normalise_rows, _is_boilerplate

COLUMN_MAP = {
    "file number": "file_number",
    "applicants name": "applicant",
    "app. type": "app_type",
    "date received": "date_received",
    "development description and location": "description",
    "eis recd.": "eis",
}


def test_map_column_exact_match():
    assert _map_column("File Number", COLUMN_MAP) == "file_number"


def test_map_column_partial_match():
    assert _map_column("EIS Recd. Extra", COLUMN_MAP) == "eis"


def test_map_column_fallback_slug():
    assert _map_column("Some New Field!", COLUMN_MAP) == "some_new_field"


def test_normalise_rows_skips_boilerplate():
    raw_rows = [
        ["File Number", "Applicants Name", "App. Type", "Date Received",
         "Development Description and Location", "EIS Recd."],
        ["24/1234", "John Smith", "P", "02/03/2026",
         "Construction of extension at 19 Monivea Road", "N"],
        ["", "Section 34 of the Planning Acts", "", "", "", ""],
    ]
    records = _normalise_rows(raw_rows, COLUMN_MAP)
    assert len(records) == 1
    assert records[0]["file_number"] == "24/1234"


def test_is_boilerplate_detects_legal_notice():
    assert _is_boilerplate("Section 34 of the Planning Acts applies")
    assert not _is_boilerplate("Construction of extension at 19 Monivea Road")
