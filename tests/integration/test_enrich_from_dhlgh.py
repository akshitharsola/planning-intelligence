import uuid

import sqlalchemy as sa

from scripts.enrich_from_dhlgh import build_enrichment_plan, apply_enrichment_plan
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


def test_apply_enrichment_plan_only_changes_planned_fields():
    session = SessionLocal()
    try:
        _cleanup(session)
        app = Application(**_base_application_kwargs(site_address=None))
        session.add(app)
        session.add(DHLGHApplication(**_base_dhlgh_kwargs(site_address="Backfilled address")))
        session.commit()

        original_ref = app.application_ref
        original_applicant = app.applicant_name
        original_status = app.planning_status_current

        plan = build_enrichment_plan(session, authority_filter="Galway County Council", ref_prefix="ENRICHTEST/")
        matching_plan = [p for p in plan if p["application_ref"] == "ENRICHTEST/001"]
        assert len(matching_plan) == 1

        updated_count = apply_enrichment_plan(session, matching_plan)

        session.expire_all()
        refreshed = session.get(Application, app.id)

        assert updated_count == 1
        assert refreshed.site_address == "Backfilled address"
        # Unrelated fields must be untouched.
        assert refreshed.application_ref == original_ref
        assert refreshed.applicant_name == original_applicant
        assert refreshed.planning_status_current == original_status
    finally:
        _cleanup(session)
        session.close()


def test_apply_enrichment_plan_with_empty_plan_does_nothing():
    session = SessionLocal()
    try:
        _cleanup(session)
        updated_count = apply_enrichment_plan(session, [])
        assert updated_count == 0
    finally:
        _cleanup(session)
        session.close()


def test_rung4_fuzzy_match_never_appears_in_plan():
    session = SessionLocal()
    try:
        _cleanup(session)
        # Create an application with a site address that is NOT a normalized
        # address match but IS similar enough for rung-4 fuzzy matching.
        # E.g. "123 Main Street" vs "123 Main St" has high trigram similarity
        # (>= 0.6) but different normalized forms.
        session.add(Application(**_base_application_kwargs(site_address="123 Main Street, Galway")))
        session.add(DHLGHApplication(**_base_dhlgh_kwargs(site_address="123 Main St, Galway")))
        session.commit()

        plan = build_enrichment_plan(session, authority_filter="Galway County Council", ref_prefix="ENRICHTEST/")
        matching = [p for p in plan if p["application_ref"] == "ENRICHTEST/001"]

        # Assert no entry appears in the plan for this ref.
        # This proves rung-4 (fuzzy) matches are excluded.
        assert matching == []
    finally:
        _cleanup(session)
        session.close()
