"""
Fixture table from spec section 9.1
(docs/superpowers/specs/2026-07-10-dhlgh-national-source-design.md) — real
refs pulled from our own `applications` table and the live DHLGH endpoint
during the design's review, not synthetic examples. Assert on this exact
table (or its evolved version) per the spec's explicit instruction.
"""

from src.core.normalization.application_ref import normalize_application_ref


def test_city_2660243_normalizes_to_slashed_form():
    assert normalize_application_ref("2660243", "Galway City Council") == "26/60243"


def test_county_26170_cannot_normalize():
    assert normalize_application_ref("26170", "Galway County Council") is None


def test_county_2661119_cannot_normalize():
    assert normalize_application_ref("2661119", "Galway County Council") is None


def test_county_163_cannot_normalize():
    assert normalize_application_ref("163", "Galway County Council") is None


def test_already_normalized_city_ref_is_idempotent():
    assert normalize_application_ref("24/60030", "Galway City Council") == "24/60030"


def test_blank_input_cannot_normalize():
    assert normalize_application_ref("", "Galway City Council") is None
    assert normalize_application_ref("   ", "Galway City Council") is None
    assert normalize_application_ref(None, "Galway City Council") is None
