import uuid

import sqlalchemy as sa

from scripts.enrich_from_dhlgh import build_enrichment_plan
from src.core.db.session import SessionLocal
from src.core.models.application import Application
from src.core.models.dhlgh_application import DHLGHApplication


def _cleanup(session):
    session.execute(sa.text("DELETE FROM applications WHERE application_ref LIKE 'ENRICHTEST/%'"))
    session.execute(sa.text("DELETE FROM dhlgh_applications WHERE application_ref LIKE 'ENRICHTEST/%'"))
    session.commit()


def _base_application_kwargs(**overrides):
    kwargs = dict(
        id=uuid.uuid4(),
        planning_authority="Galway County Council",
        source_entity="GALWAY_COUNTY",
        application_ref="ENRICHTEST/001",
        applicant_name="Test",
        site_address=None,
        development_description="Test",
        application_type="Permission",
        planning_status_current="Received",
        date_received="2026-01-01",
        source_system="test",
        source_file="test",
    )
    kwargs.update(overrides)
    return kwargs


def _base_dhlgh_kwargs(**overrides):
    kwargs = dict(
        id=uuid.uuid4(),
        planning_authority="Galway County Council",
        source_entity="DHLGH_NATIONAL",
        application_ref="ENRICHTEST/001",
        development_description="Test",
        site_address="Test address one",
        planning_status_current="Received",
        date_received="2026-01-01",
        source_system="test",
    )
    kwargs.update(overrides)
    return kwargs


def test_rung1_match_plans_site_address_backfill_only_when_null():
    session = SessionLocal()
    try:
        _cleanup(session)
        session.add(Application(**_base_application_kwargs()))
        session.add(DHLGHApplication(**_base_dhlgh_kwargs()))
        session.commit()

        plan = build_enrichment_plan(session, authority_filter="Galway County Council", ref_prefix="ENRICHTEST/")
        matching = [p for p in plan if p["application_ref"] == "ENRICHTEST/001"]

        assert len(matching) == 1
        assert matching[0]["field"] == "site_address"
        assert matching[0]["new_value"] == "Test address one"
        assert matching[0]["rung"] == 1
    finally:
        _cleanup(session)
        session.close()


def test_no_plan_when_our_site_address_already_non_null():
    session = SessionLocal()
    try:
        _cleanup(session)
        session.add(Application(**_base_application_kwargs(site_address="Already populated")))
        session.add(DHLGHApplication(**_base_dhlgh_kwargs()))
        session.commit()

        plan = build_enrichment_plan(session, authority_filter="Galway County Council", ref_prefix="ENRICHTEST/")
        matching = [p for p in plan if p["application_ref"] == "ENRICHTEST/001"]

        assert matching == []
    finally:
        _cleanup(session)
        session.close()
