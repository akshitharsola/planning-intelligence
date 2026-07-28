import uuid
from unittest.mock import MagicMock

from scripts.enrich_from_dhlgh import build_enrichment_plan


def _make_session_with_rows(app_rows, dhlgh_rows):
    session = MagicMock()

    def scalars_side_effect(query):
        query_str = str(query)
        result = MagicMock()
        if "dhlgh_applications" in query_str:
            result.all.return_value = dhlgh_rows
        else:
            result.all.return_value = app_rows
        return result

    session.scalars.side_effect = scalars_side_effect
    return session


class FakeApplication:
    def __init__(self, id, application_ref, site_address, site_geometry, planning_authority):
        self.id = id
        self.application_ref = application_ref
        self.site_address = site_address
        self.site_geometry = site_geometry
        self.planning_authority = planning_authority


class FakeDHLGH:
    def __init__(self, application_ref, site_address, site_geometry, planning_authority):
        self.application_ref = application_ref
        self.site_address = site_address
        self.site_geometry = site_geometry
        self.planning_authority = planning_authority


def test_rung1_match_with_null_site_address_produces_planned_update():
    app_id = uuid.uuid4()
    app = FakeApplication(app_id, "17792", None, None, "Galway County Council")
    dhlgh = FakeDHLGH("17792", "Cahernamona, Co. Galway", None, "Galway County Council")

    session = _make_session_with_rows([app], [dhlgh])
    plan = build_enrichment_plan(session, authority_filter="Galway County Council")

    assert len(plan) == 1
    assert plan[0]["application_id"] == app_id
    assert plan[0]["field"] == "site_address"
    assert plan[0]["new_value"] == "Cahernamona, Co. Galway"
    assert plan[0]["rung"] == 1


def test_match_with_non_null_site_address_produces_no_planned_update_for_that_field():
    app_id = uuid.uuid4()
    app = FakeApplication(app_id, "17792", "Already has an address", None, "Galway County Council")
    dhlgh = FakeDHLGH("17792", "Cahernamona, Co. Galway", None, "Galway County Council")

    session = _make_session_with_rows([app], [dhlgh])
    plan = build_enrichment_plan(session, authority_filter="Galway County Council")

    assert plan == []


def test_no_match_produces_no_planned_update():
    app = FakeApplication(uuid.uuid4(), "17792", None, None, "Galway County Council")
    dhlgh = FakeDHLGH("99999", "Unrelated address", None, "Galway County Council")

    session = _make_session_with_rows([app], [dhlgh])
    plan = build_enrichment_plan(session, authority_filter="Galway County Council")

    assert plan == []


def test_ambiguous_match_produces_no_planned_update():
    app1 = FakeApplication(uuid.uuid4(), "17792", None, None, "Galway County Council")
    app2 = FakeApplication(uuid.uuid4(), "17792", None, None, "Galway County Council")
    dhlgh = FakeDHLGH("17792", "Cahernamona, Co. Galway", None, "Galway County Council")

    session = _make_session_with_rows([app1, app2], [dhlgh])
    plan = build_enrichment_plan(session, authority_filter="Galway County Council")

    assert plan == []


def test_two_distinct_dhlgh_rows_matching_same_application_field_are_both_dropped():
    # Two DHLGH rows with different refs but the same normalized address
    # each independently resolve to the same single applications row at
    # rung 2. Applying both would let list order silently pick a winner
    # (a real bug found in manual verification) - both must be dropped
    # instead of one clobbering the other.
    app_id = uuid.uuid4()
    app = FakeApplication(app_id, "23/60037", "Quarry Road Menlo Galway", None, "Galway City Council")
    dhlgh1 = FakeDHLGH("1711", "Quarry Road Menlo Galway", "geom-a", "Galway City Council")
    dhlgh2 = FakeDHLGH("20142", "Quarry Road Menlo Galway", "geom-b", "Galway City Council")

    session = _make_session_with_rows([app], [dhlgh1, dhlgh2])
    plan = build_enrichment_plan(session, authority_filter="Galway City Council")

    assert plan == []
