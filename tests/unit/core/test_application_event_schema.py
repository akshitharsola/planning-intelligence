from src.core.schemas.application_event import ApplicationEventCreate


def test_application_event_create():
    event = ApplicationEventCreate(
        application_ref="24/1234",
        planning_authority="Galway City Council",
        event_type="APPLICATION_RECEIVED",
        event_date="2026-03-02",
        source_file="Weekly Lists - Planning Applications Received.pdf",
    )
    assert event.event_type == "APPLICATION_RECEIVED"
