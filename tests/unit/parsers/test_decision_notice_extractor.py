from pathlib import Path
import pytest

from src.parsers.decision_notice.extractor import (
    has_text_layer,
    parse_notice,
    ParsedItem,
    ParsedNotice,
)

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "decision_notices"


def read_fixture(name: str) -> str:
    path = FIXTURES_DIR / f"{name}.txt"
    return path.read_text(encoding="utf-8")


def test_blank_text_is_not_text_layer():
    assert not has_text_layer("")
    assert not has_text_layer("   \n\n\t  \n")
    assert not has_text_layer("line 1\nline 2\nline 3\n")
    assert has_text_layer("l1\nl2\nl3\nl4\nl5\n")


def test_fixture_2360654_refusal_four_reasons():
    text = read_fixture("2360654_2469775")
    parsed = parse_notice(text, authority="Galway County Council", decision="REFUSED")
    assert parsed.status == "validated"
    assert len(parsed.items) == 4
    assert parsed.stated_count == 4
    assert parsed.target_count == 4
    assert parsed.kind == "refusal_reason"
    assert parsed.failure_reason is None


def test_fixture_2260277_grant_17_conditions():
    text = read_fixture("2260277_2378606")
    parsed = parse_notice(text, authority="Galway County Council", decision="CONDITIONAL")
    assert parsed.status == "validated"
    assert len(parsed.items) == 17
    assert parsed.stated_count == 17
    assert parsed.target_count == 17
    assert parsed.kind == "condition"


def test_fixture_2561413_grant_9_c3():
    text = read_fixture("2561413_2669234")
    parsed = parse_notice(text, authority="Galway County Council", decision="CONDITIONAL")
    assert parsed.status == "validated"
    assert len(parsed.items) == 9
    assert parsed.stated_count == 9
    assert parsed.target_count == 9
    assert parsed.kind == "condition"


def test_fixture_2261158_single_unnumbered_reason():
    text = read_fixture("2261158_2429146")
    parsed = parse_notice(text, authority="Galway County Council", decision="REFUSED")
    assert parsed.status == "validated"
    assert len(parsed.items) == 1
    assert parsed.stated_count == 1
    assert parsed.target_count == 1
    assert parsed.kind == "refusal_reason"


def test_fixture_24155_extension_of_duration_inline_refusal():
    text = read_fixture("24155_2549490")
    parsed = parse_notice(text, authority="Galway County Council", decision="REFUSED")
    assert parsed.status == "validated"
    assert len(parsed.items) == 1
    assert parsed.stated_count == 1
    assert parsed.target_count == 1
    assert parsed.kind == "refusal_reason"


def test_fixture_2561329_count_mismatch_13_vs_14():
    text = read_fixture("2561329_2665281")
    parsed = parse_notice(text, authority="Galway County Council", decision="CONDITIONAL")
    assert parsed.status == "count_mismatch"
    assert len(parsed.items) == 13
    assert parsed.stated_count == 14
    assert parsed.target_count == 14
    assert parsed.failure_reason == "Parsed 13 items vs target 14"


def test_fixture_2660157_count_mismatch_3_vs_2():
    text = read_fixture("2660157_2699960")
    parsed = parse_notice(text, authority="Galway County Council", decision="REFUSED")
    assert parsed.status == "count_mismatch"
    assert len(parsed.items) == 3
    assert parsed.stated_count == 2
    assert parsed.target_count == 2
    assert parsed.failure_reason == "Parsed 3 items vs target 2"


def test_fixture_2360744_no_schedule():
    text = read_fixture("2360744_2474243")
    parsed = parse_notice(text, authority="Galway County Council", eplan_count=2, decision="REFUSED")
    assert parsed.status == "no_schedule"
    assert len(parsed.items) == 0
    assert parsed.stated_count is None
    assert parsed.target_count == 2
    assert parsed.failure_reason is not None


def test_footnote_steps_not_counted():
    text = read_fixture("2360654_2469775")
    parsed = parse_notice(text, authority="Galway County Council", decision="REFUSED")
    assert len(parsed.items) == 4
    for item in parsed.items:
        assert "You have four weeks" not in item.text


def test_reason_line_split_for_grants():
    text = read_fixture("2260277_2378606")
    parsed = parse_notice(text, authority="Galway County Council", decision="CONDITIONAL")
    assert len(parsed.items) == 17
    item1 = parsed.items[0]
    assert item1.n == 1
    assert item1.reason_text is not None
    assert len(item1.reason_text.strip()) > 0


def test_unverified_when_target_count_missing():
    import re
    text = read_fixture("2561329_2665281")
    text_no_count = re.sub(r"conditions?\s+\d+\s+set\s+out", "conditions set out", text, flags=re.I)
    text_no_count = re.sub(r"\(CONDITION\s*NO[\s.’\x27]*S\s*\d+\)", "", text_no_count, flags=re.I)

    parsed = parse_notice(text_no_count, authority="Galway County Council", eplan_count=None, decision="CONDITIONAL")
    assert parsed.status == "unverified"
    assert parsed.status != "validated"
    assert len(parsed.items) == 13
    assert parsed.stated_count is None
    assert parsed.target_count is None
    assert parsed.failure_reason == "No stated or ePlanning count to validate against"


def test_extension_of_duration_inline_refusal_pins_single_item():
    text = read_fixture("24155_2549490")
    # With no stated count and eplan_count=None, target defaults to 1 and validates as exactly 1 item
    parsed = parse_notice(text, authority="Galway County Council", eplan_count=None, decision="REFUSED")
    assert parsed.status == "validated"
    assert len(parsed.items) == 1
    assert parsed.target_count == 1
    assert parsed.kind == "refusal_reason"

    # When an external count expects > 1, single inline item results in count_mismatch
    parsed_mismatch = parse_notice(text, authority="Galway County Council", eplan_count=2, decision="REFUSED")
    assert parsed_mismatch.status == "count_mismatch"
    assert len(parsed_mismatch.items) == 1
    assert parsed_mismatch.target_count == 2
