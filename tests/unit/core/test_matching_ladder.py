import uuid

import sqlalchemy as sa

from src.core.db.session import SessionLocal
from src.core.matching.ladder import (
    MatchCandidate,
    rung1_ref_match,
    rung2_address_match,
    rung3_geometry_match,
)
from src.core.models.application import Application


def test_rung1_matches_unique_exact_county_ref():
    # Real confirmed match pulled live from the DB during planning:
    # applications and dhlgh_applications both have planning_authority
    # "Galway County Council", application_ref "17792".
    candidates = [
        MatchCandidate(application_ref="17792", site_address="Cahernamona ,", site_geometry_wkt=None),
        MatchCandidate(application_ref="20651", site_address="Ardgaineen , Claregalway", site_geometry_wkt=None),
    ]
    result = rung1_ref_match("17792", "Galway County Council", candidates)
    assert result.matched is True
    assert result.rung == 1
    assert result.ambiguous is False


def test_rung1_no_match_when_ref_absent():
    candidates = [
        MatchCandidate(application_ref="20651", site_address="Ardgaineen , Claregalway", site_geometry_wkt=None),
    ]
    result = rung1_ref_match("99999", "Galway County Council", candidates)
    assert result.matched is False
    assert result.ambiguous is False


def test_rung1_ambiguous_when_ref_appears_twice():
    # Duplicate refs would only occur if the natural-key constraint were
    # ever bypassed — the ladder must not assume it can't happen and must
    # treat >1 candidate as ambiguous, not as a match.
    candidates = [
        MatchCandidate(application_ref="17792", site_address="Cahernamona ,", site_geometry_wkt=None),
        MatchCandidate(application_ref="17792", site_address="Duplicate entry", site_geometry_wkt=None),
    ]
    result = rung1_ref_match("17792", "Galway County Council", candidates)
    assert result.matched is False
    assert result.ambiguous is True


def test_rung1_normalizes_city_dhlgh_ref_before_comparing():
    # Real City case confirmed live: DHLGH's raw "2660243" for Galway City
    # Council normalizes (via normalize_application_ref) to "26/60243",
    # which is the shape our own applications.application_ref already uses
    # (confirmed: 525/527 City refs match ^\d{2}/\d+$).
    candidates = [
        MatchCandidate(application_ref="26/60243", site_address="7 Lower Canal Road, Galway", site_geometry_wkt=None),
    ]
    result = rung1_ref_match("2660243", "Galway City Council", candidates)
    assert result.matched is True
    assert result.rung == 1


def test_rung1_no_match_when_ref_cannot_normalize_and_no_raw_equal():
    # Real County case: normalize_application_ref("2661119", "Galway County
    # Council") returns None (documented ambiguous shape, spec section
    # 9.1). Rung 1 must fall back to comparing the raw string as-is, and
    # here it also has no equal candidate, so it's a clean no-match, not
    # an error.
    candidates = [
        MatchCandidate(application_ref="26170", site_address="", site_geometry_wkt=None),
    ]
    result = rung1_ref_match("2661119", "Galway County Council", candidates)
    assert result.matched is False
    assert result.ambiguous is False


def test_rung2_matches_unique_address_after_normalization():
    # Real variant forms confirmed live: our own site_address strings use
    # "Co. Galway" / "Co Galway" / trailing "Galway"; DHLGH's
    # DevelopmentAddress uses the same variants inconsistently. Both
    # normalize to "ardgaineen".
    candidates = [
        MatchCandidate(application_ref="X", site_address="Ardgaineen, Co. Galway", site_geometry_wkt=None),
    ]
    result = rung2_address_match("Ardgaineen, Galway", candidates)
    assert result.matched is True
    assert result.rung == 2


def test_rung2_no_match_when_addresses_differ():
    candidates = [
        MatchCandidate(application_ref="X", site_address="Townparks, Co. Galway", site_geometry_wkt=None),
    ]
    result = rung2_address_match("Ardgaineen, Galway", candidates)
    assert result.matched is False
    assert result.ambiguous is False


def test_rung2_ambiguous_when_two_candidates_share_normalized_address():
    candidates = [
        MatchCandidate(application_ref="X", site_address="Ardgaineen, Co. Galway", site_geometry_wkt=None),
        MatchCandidate(application_ref="Y", site_address="Ardgaineen Co Galway", site_geometry_wkt=None),
    ]
    result = rung2_address_match("Ardgaineen, Galway", candidates)
    assert result.matched is False
    assert result.ambiguous is True


def test_rung2_no_match_when_dhlgh_address_is_none():
    candidates = [
        MatchCandidate(application_ref="X", site_address="Ardgaineen, Co. Galway", site_geometry_wkt=None),
    ]
    result = rung2_address_match(None, candidates)
    assert result.matched is False
    assert result.ambiguous is False


def _make_application(session, application_ref, lon, lat):
    app = Application(
        id=uuid.uuid4(),
        planning_authority="Galway County Council",
        source_entity="GALWAY_COUNTY",
        application_ref=application_ref,
        applicant_name="Test",
        site_address="Test address",
        development_description="Test",
        application_type="Permission",
        planning_status_current="Received",
        date_received="2026-01-01",
        source_system="test",
        source_file="test",
        site_geometry=f"SRID=4326;POINT({lon} {lat})",
    )
    session.add(app)
    return app


def test_rung3_matches_point_within_proximity_radius():
    session = SessionLocal()
    try:
        session.execute(sa.text("DELETE FROM applications WHERE application_ref LIKE 'GEOMTEST/%'"))
        _make_application(session, "GEOMTEST/001", -9.0568, 53.2707)
        session.commit()

        # A point ~5 meters away from the seeded row (well within 25m).
        result = rung3_geometry_match(
            session,
            "SRID=4326;POINT(-9.05675 53.27074)",
            "Galway County Council",
        )
        assert result.matched is True
        assert result.rung == 3
    finally:
        session.execute(sa.text("DELETE FROM applications WHERE application_ref LIKE 'GEOMTEST/%'"))
        session.commit()
        session.close()


def test_rung3_ambiguous_when_two_candidates_within_radius():
    session = SessionLocal()
    try:
        session.execute(sa.text("DELETE FROM applications WHERE application_ref LIKE 'GEOMTEST/%'"))
        # Two distinct applications a few meters apart, both within the
        # default 25m proximity radius of the query point below.
        _make_application(session, "GEOMTEST/002", -9.0568, 53.2707)
        _make_application(session, "GEOMTEST/003", -9.05682, 53.27072)
        session.commit()

        result = rung3_geometry_match(
            session,
            "SRID=4326;POINT(-9.05678 53.27071)",
            "Galway County Council",
        )
        assert result.matched is False
        assert result.ambiguous is True
    finally:
        session.execute(sa.text("DELETE FROM applications WHERE application_ref LIKE 'GEOMTEST/%'"))
        session.commit()
        session.close()


def test_rung3_no_match_when_no_geometry_on_dhlgh_side():
    session = SessionLocal()
    try:
        result = rung3_geometry_match(session, None, "Galway County Council")
        assert result.matched is False
        assert result.ambiguous is False
    finally:
        session.close()


def test_rung3_no_match_when_no_candidates_have_geometry():
    # Reflects real current state: applications.site_geometry is 0%
    # populated (confirmed live: 0 of 20,902 rows), so this rung must
    # cleanly report no-match rather than error when the whole table has
    # no geometry to compare against.
    session = SessionLocal()
    try:
        result = rung3_geometry_match(
            session,
            "SRID=4326;POINT(-9.0568 53.2707)",
            "Galway County Council",
        )
        assert result.matched is False
    finally:
        session.close()
