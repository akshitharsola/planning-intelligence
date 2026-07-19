import pytest

from src.core.normalization.dhlgh import normalize_dhlgh_row

REGION_CONFIG = {
    "source_entity": "DHLGH_NATIONAL",
}


def test_normalize_dhlgh_row_basic_fields():
    raw_row = {
        "OBJECTID": 269810,
        "PlanningAuthority": "Galway City Council",
        "ApplicationNumber": "2012",
        "DevelopmentDescription": "Permission for installation of an ATM machine",
        "DevelopmentAddress": "The Huntsman Inn , 164 College Road , Galway",
        "DevelopmentPostcode": "",
        "ApplicationStatus": "Granted",
        "ApplicationType": "Permission",
        "Decision": "Granted",
        "ReceivedDate": 1580083200000,
    }
    app = normalize_dhlgh_row(raw_row, region_config=REGION_CONFIG, source_file="dhlgh:269810")
    assert app.planning_authority == "Galway City Council"
    assert app.application_ref == "2012"
    assert app.site_postcode is None
    assert app.site_address == "The Huntsman Inn , 164 College Road , Galway"
    assert app.date_received.isoformat() == "2020-01-27"


def test_normalize_dhlgh_row_empty_postcode_is_not_an_error():
    raw_row = {
        "OBJECTID": 1,
        "PlanningAuthority": "Galway County Council",
        "ApplicationNumber": "26170",
        "DevelopmentDescription": "test",
        "DevelopmentAddress": "Oranmore",
        "DevelopmentPostcode": "",
        "ApplicationStatus": "Received",
        "ReceivedDate": 1580083200000,
    }
    app = normalize_dhlgh_row(raw_row, region_config=REGION_CONFIG, source_file="dhlgh:1")
    assert app.site_postcode is None


def test_normalize_dhlgh_row_appeal_fields_present():
    raw_row = {
        "OBJECTID": 2,
        "PlanningAuthority": "Galway City Council",
        "ApplicationNumber": "24/60030",
        "DevelopmentDescription": "test",
        "ApplicationStatus": "Refused",
        "ReceivedDate": 1580083200000,
        "AppealRefNumber": "ABP-123456-25",
        "AppealStatus": "Determined",
        "AppealDecision": "Refuse Permission",
        "AppealDecisionDate": 1600000000000,
        "AppealSubmittedDate": 1590000000000,
    }
    app = normalize_dhlgh_row(raw_row, region_config=REGION_CONFIG, source_file="dhlgh:2")
    assert app.appeal_ref_number == "ABP-123456-25"
    assert app.appeal_status == "Determined"
    assert app.appeal_decision == "Refuse Permission"
    assert app.appeal_decision_date is not None
    assert app.appeal_submitted_date is not None


def test_normalize_dhlgh_row_appeal_fields_absent():
    raw_row = {
        "OBJECTID": 3,
        "PlanningAuthority": "Galway City Council",
        "ApplicationNumber": "24/60031",
        "DevelopmentDescription": "test",
        "ApplicationStatus": "Received",
        "ReceivedDate": 1580083200000,
    }
    app = normalize_dhlgh_row(raw_row, region_config=REGION_CONFIG, source_file="dhlgh:3")
    assert app.appeal_ref_number is None
    assert app.appeal_status is None
    assert app.appeal_decision is None
    assert app.appeal_decision_date is None
    assert app.appeal_submitted_date is None


def test_normalize_dhlgh_row_geometry_present():
    raw_row = {
        "OBJECTID": 4,
        "PlanningAuthority": "Galway City Council",
        "ApplicationNumber": "24/60032",
        "DevelopmentDescription": "test",
        "ApplicationStatus": "Received",
        "ReceivedDate": 1580083200000,
        "_geometry": {
            "rings": [
                [
                    [-9.034, 53.281],
                    [-9.033, 53.282],
                    [-9.032, 53.281],
                    [-9.034, 53.281],
                ]
            ]
        },
    }
    app = normalize_dhlgh_row(raw_row, region_config=REGION_CONFIG, source_file="dhlgh:4")
    assert app.site_geometry is not None
    assert app.site_geometry.startswith("SRID=4326;POLYGON")


def test_normalize_dhlgh_row_geometry_absent():
    raw_row = {
        "OBJECTID": 5,
        "PlanningAuthority": "Galway City Council",
        "ApplicationNumber": "24/60033",
        "DevelopmentDescription": "test",
        "ApplicationStatus": "Received",
        "ReceivedDate": 1580083200000,
    }
    app = normalize_dhlgh_row(raw_row, region_config=REGION_CONFIG, source_file="dhlgh:5")
    assert app.site_geometry is None


def test_normalize_dhlgh_row_date_parsing_string_format():
    raw_row = {
        "OBJECTID": 6,
        "PlanningAuthority": "Galway County Council",
        "ApplicationNumber": "26/6",
        "DevelopmentDescription": "test",
        "ApplicationStatus": "Received",
        "ReceivedDate": "01/03/2026",
        "DecisionDate": "15/04/2026",
    }
    app = normalize_dhlgh_row(raw_row, region_config=REGION_CONFIG, source_file="dhlgh:6")
    assert app.date_received.isoformat() == "2026-03-01"
    assert app.decision_date.isoformat() == "2026-04-15"


def test_normalize_dhlgh_row_rejects_missing_application_number():
    raw_row = {
        "OBJECTID": 7,
        "PlanningAuthority": "Galway City Council",
        "ApplicationNumber": None,
        "DevelopmentDescription": "test",
        "ApplicationStatus": "Received",
        "ReceivedDate": 1580083200000,
    }
    with pytest.raises(ValueError, match="ApplicationNumber"):
        normalize_dhlgh_row(raw_row, region_config=REGION_CONFIG, source_file="dhlgh:7")
