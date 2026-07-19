from src.core.matching.ladder import MatchCandidate, rung1_ref_match, rung2_address_match


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
