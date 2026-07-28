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
        # Distinct application_refs so rung 1 cannot match. site_address is
        # non-null on both sides (rung 4's own query requires a non-null
        # Application.site_address to be reachable at all - see
        # rung4_fuzzy_match in src/core/matching/ladder.py) but the two
        # addresses normalize identically, so rung 2 also cannot match: only
        # rung 4 (trigram fuzzy) can resolve this pair. "123 Maim Street" vs
        # "123 Main Street" has trigram similarity ~0.84, above the rung-4
        # threshold (0.6), but normalize_address() does not fix the typo, so
        # the normalized forms differ - confirmed this pair resolves at rung
        # 4 via a direct run_ladder probe against real Postgres.
        #
        # site_geometry is null on our side and non-null on DHLGH's side, so
        # it is the actual discriminator here: a bug that let rung 4 write
        # would populate site_geometry (since site_address is already
        # non-null and blocked by the overwrite-null-only guard on its own).
        # Confirmed via mutation testing (disabling both the outer rung
        # filter and _find_matched_candidate's rung restriction) that this
        # test fails - a site_geometry entry appears in the plan - when rung
        # 4 is wrongly allowed to write, before trusting this assertion.
        session.add(Application(**_base_application_kwargs(
            site_address="123 Maim Street, Galway", site_geometry=None,
        )))
        session.add(DHLGHApplication(**_base_dhlgh_kwargs(
            application_ref="ENRICHTEST/999",
            site_address="123 Main Street, Galway",
            site_geometry="SRID=4326;POINT(-9.05 53.27)",
        )))
        session.commit()

        plan = build_enrichment_plan(session, authority_filter="Galway County Council", ref_prefix="ENRICHTEST/")
        matching = [p for p in plan if p["application_ref"] == "ENRICHTEST/001"]

        # Assert no entry appears in the plan for this ref.
        # This proves rung-4 (fuzzy) matches are excluded.
        assert matching == []
    finally:
        _cleanup(session)
        session.close()
