import pytest
from pydantic import ValidationError

from src.core.schemas.application import ApplicationCreate


def test_application_create_requires_natural_key():
    app = ApplicationCreate(
        planning_authority="Galway City Council",
        source_entity="GALWAY_CITY_COUNCIL",
        application_ref="24/1234",
        applicant_name="John Smith",
        development_description="Construction of extension at 19 Monivea Road",
        application_type="Permission",
        planning_status_current="Received",
        date_received="2026-03-02",
        source_system="Galway City Weekly Lists PDF",
        source_file="Weekly Lists - Planning Applications Received.pdf",
    )
    assert app.application_ref == "24/1234"
    assert app.market_entity is None


def test_application_create_rejects_missing_application_ref():
    with pytest.raises(ValidationError):
        ApplicationCreate(
            planning_authority="Galway City Council",
            source_entity="GALWAY_CITY_COUNCIL",
            applicant_name="John Smith",
            development_description="x",
            application_type="Permission",
            planning_status_current="Received",
            date_received="2026-03-02",
            source_system="Galway City Weekly Lists PDF",
            source_file="x.pdf",
        )


def test_application_create_accepts_eircode():
    app = ApplicationCreate(
        planning_authority="Galway City Council",
        source_entity="GALWAY_CITY_COUNCIL",
        application_ref="24/0001",
        applicant_name="Test Applicant",
        development_description="test",
        application_type="PERMISSION",
        planning_status_current="Received",
        date_received="2026-01-01",
        source_system="test",
        source_file="test.pdf",
        eircode="H91WE0R",
    )
    assert app.eircode == "H91WE0R"


def test_application_create_eircode_defaults_to_none():
    app = ApplicationCreate(
        planning_authority="Galway City Council",
        source_entity="GALWAY_CITY_COUNCIL",
        application_ref="24/0002",
        applicant_name="Test Applicant",
        development_description="test",
        application_type="PERMISSION",
        planning_status_current="Received",
        date_received="2026-01-01",
        source_system="test",
        source_file="test.pdf",
    )
    assert app.eircode is None
