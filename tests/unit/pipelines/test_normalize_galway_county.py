from src.core.normalization.galway_county import normalize_county_row

REGION_CONFIG = {
    "source_entity": "GALWAY_COUNTY_COUNCIL",
    "planning_authority": "Galway County Council",
}


def test_normalize_county_row_received():
    raw_row = {
        "OBJECTID": 173999,
        "ApplicationNumber": "26/9999",
        "ApplicantName": "Mary Byrne",
        "ApplicationType": "PERMISSION",
        "ApplicationStatus": "Application Pending",
        "ReceivedDate": "03/03/2026",
        "Decision": "n\\a",
        "Location": "Oranmore",
        "Description": "New dwelling at Oranmore Co. Galway",
    }
    app = normalize_county_row(raw_row, region_config=REGION_CONFIG, source_file="arcgis:173999")
    assert app.application_ref == "26/9999"
    assert app.planning_authority == "Galway County Council"
    assert app.planning_status_current == "Received"
    assert app.status_event_type == "APPLICATION_RECEIVED"
    assert app.site_county == "Galway"


def test_normalize_county_row_granted():
    raw_row = {
        "OBJECTID": 173622,
        "ApplicationNumber": "18229",
        "ApplicantName": "Wayne Gibbons",
        "ApplicationType": "RETENTION",
        "ApplicationStatus": "Application Finalised",
        "ReceivedDate": "28/02/2018",
        "Decision": "Granted (Conditional)",
        "DecisionDate": "20/04/2018",
        "Location": "Laraghmore",
        "Description": "garage and store to rear of dwelling",
    }
    app = normalize_county_row(raw_row, region_config=REGION_CONFIG, source_file="arcgis:173622")
    assert app.planning_status_current == "Granted"
    assert app.status_event_type == "DECISION_GRANTED"
    assert app.decision_date.isoformat() == "2018-04-20"


def test_normalize_county_row_withdrawn():
    raw_row = {
        "OBJECTID": 1,
        "ApplicationNumber": "20/1",
        "ApplicantName": "Test Applicant",
        "ApplicationType": "PERMISSION",
        "ApplicationStatus": "Withdrawn",
        "ReceivedDate": "01/01/2020",
        "Decision": "n\\a",
        "Location": "Tuam",
        "Description": "test",
    }
    app = normalize_county_row(raw_row, region_config=REGION_CONFIG, source_file="arcgis:1")
    assert app.planning_status_current == "Withdrawn"
    assert app.status_event_type == "APPLICATION_WITHDRAWN"
