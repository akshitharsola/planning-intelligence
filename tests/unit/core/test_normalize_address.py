from src.core.normalization.address import normalize_address


def test_lowercases_and_strips_punctuation():
    assert normalize_address("15 Emerson Avenue, Salthill, Galway") == "15 emerson avenue salthill"


def test_co_galway_variants_all_equivalent():
    a = normalize_address("Tonagarraun, Corrandulla, Co. Galway")
    b = normalize_address("Tonagarraun, Corrandulla, Co Galway")
    c = normalize_address("Tonagarraun, Corrandulla, County Galway")
    assert a == b == c == "tonagarraun corrandulla"


def test_collapses_whitespace():
    assert normalize_address("  7   Lower   Canal  Road  ") == "7 lower canal road"


def test_rd_and_st_abbreviations_expand():
    assert normalize_address("7 Lower Canal Rd") == "7 lower canal road"
    assert normalize_address("1 Main St") == "1 main street"


def test_trailing_galway_token_dropped_when_rest_nonempty():
    assert normalize_address("7 Lower Canal Road, Galway") == "7 lower canal road"


def test_standalone_galway_not_dropped_to_empty_string():
    # Rest of string would be empty after stripping trailing "galway" —
    # keep the token rather than return an empty normalized address.
    assert normalize_address("Galway") == "galway"


def test_hyphenated_place_name_hyphen_preserved():
    assert normalize_address("Cul-de-sac House, Galway") == "cul-de-sac house"


def test_two_addresses_from_different_sources_match_after_normalization():
    dhlgh = "15 Emerson Avenue , Salthill , Galway"
    ours = "15 Emerson Avenue, Salthill"
    assert normalize_address(dhlgh) == normalize_address(ours)
