import pytest

from src.pipelines.normalize import normalize_row

REGION_CONFIG = {
    "source_entity": "GALWAY_CITY_COUNCIL",
    "planning_authority": "Galway City Council",
}


def test_normalize_row_received_maps_to_application_received_event():
    raw_row = {
        "file_number": "24/1234",
        "applicant": "John Smith",
        "app_type": "P",
        "date_received": "02/03/2026",
        "description": "Construction of extension at 19 Monivea Road Mervue Galway",
        "eis": "N",
        "protected_structure": "N",
    }
    app = normalize_row(raw_row, source_type="received", region_config=REGION_CONFIG,
                        source_file="Weekly Lists - Planning Applications Received.pdf")
    assert app.application_ref == "24/1234"
    assert app.planning_status_current == "Received"
    assert app.status_event_type == "APPLICATION_RECEIVED"
    assert app.site_locality == "Mervue"
    assert app.further_information_flag is False
    assert app.eia_eis_flag is False


def test_normalize_row_granted_sets_decision_fields():
    raw_row = {
        "file_number": "24/5678",
        "applicant": "Jane Doe",
        "app_type": "P",
        "description": "Retention of shed at Bohermore Galway",
        "mo_date": "10/03/2026",
        "mo_number": "456",
    }
    app = normalize_row(raw_row, source_type="granted", region_config=REGION_CONFIG,
                        source_file="Weekly Lists - Planning Applications Granted.pdf")
    assert app.planning_status_current == "Granted"
    assert app.status_event_type == "DECISION_GRANTED"
    assert app.decision_date is not None


def test_normalize_row_rejects_missing_file_number():
    raw_row = {
        "applicant": "Test Applicant",
        "app_type": "P",
        "description": "test",
    }
    with pytest.raises(ValueError, match="file_number"):
        normalize_row(raw_row, source_type="received", region_config=REGION_CONFIG,
                      source_file="Weekly Lists - Planning Applications Received.pdf")


def test_normalize_row_rejects_blank_file_number():
    raw_row = {
        "file_number": "   ",
        "applicant": "Test Applicant",
        "app_type": "P",
        "description": "test",
    }
    with pytest.raises(ValueError, match="file_number"):
        normalize_row(raw_row, source_type="received", region_config=REGION_CONFIG,
                      source_file="Weekly Lists - Planning Applications Received.pdf")
