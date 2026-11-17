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


# --- parser v2 fixes (synthetic notices only; no real notice text) ---

def _grant_notice(schedule_body: str, count: int, signature: str = "Signed this 01st day of January 2026") -> str:
    return (
        "GALWAY COUNTY COUNCIL\n"
        "NOTIFICATION OF DECISION\n"
        "Planning Reference: TEST/0001\n"
        f"(CONDITION NO'S {count})\n"
        "Decision: GRANT subject to the conditions set out in the Schedule.\n"
        "\n"
        "Schedule Referred To - Planning Reference No. TEST/0001\n"
        "\n"
        f"{schedule_body}\n"
        "\n"
        f"{signature}\n"
        "for Senior Planner\n"
    )


def test_condition_line_starting_signed_and_dated_is_not_treated_as_signature():
    body = (
        "1. The development shall be carried out in accordance with the plans.\n"
        "Reason: In the interest of clarity.\n"
        "\n"
        "2. (a) A maintenance contract for the test system shall be kept in place at all times.\n"
        "Signed and dated copies of the contract shall be made available on request.\n"
        "(b) Any fill material imported on site must be free of invasive species.\n"
        "Reason: In the interest of public health.\n"
        "\n"
        "3. Services shall be laid underground.\n"
        "Reason: In the interest of visual amenity."
    )
    parsed = parse_notice(_grant_notice(body, 3), authority="Galway County Council", decision="CONDITIONAL")
    assert parsed.status == "validated"
    item2 = parsed.items[1]
    assert "Signed and dated copies of the contract shall be made available on request." in item2.text
    assert item2.text.endswith("free of invasive species.")
    assert item2.reason_text == "In the interest of public health."


@pytest.mark.parametrize(
    "signature",
    [
        "Signed this 01st day of January 2026",
        "SIGNED: ____________________",
        "SIGNED THIS 4th DAY OF MAY 2026",
        "Signed the 3rd day of March 2026",
        "Signed 12 day of June 2026",
    ],
)
def test_real_signature_lines_still_end_the_last_item(signature):
    body = (
        "1. The development shall be carried out in accordance with the plans.\n"
        "Reason: In the interest of clarity."
    )
    parsed = parse_notice(_grant_notice(body, 1, signature=signature), authority="Galway County Council", decision="CONDITIONAL")
    assert parsed.status == "validated"
    assert parsed.items[0].reason_text == "In the interest of clarity."
    assert "for Senior Planner" not in parsed.items[0].reason_text


@pytest.mark.parametrize("label", ["REASON In", "Reason In", "Reason in", "Reason; In"])
def test_reason_label_without_colon_is_split_out(label):
    body = (
        "1. The roof shall be finished in dark grey slate.\n"
        f"{label} the interest of visual amenity."
    )
    parsed = parse_notice(_grant_notice(body, 1), authority="Galway County Council", decision="CONDITIONAL")
    item = parsed.items[0]
    assert item.text == "The roof shall be finished in dark grey slate."
    assert item.reason_text.lower() == "in the interest of visual amenity."


def test_word_reason_inside_condition_text_is_not_a_label():
    body = (
        "1. The house shall not be used for any reason other than as a dwelling.\n"
        "Reason: In the interest of orderly development."
    )
    parsed = parse_notice(_grant_notice(body, 1), authority="Galway County Council", decision="CONDITIONAL")
    assert parsed.items[0].text == "The house shall not be used for any reason other than as a dwelling."
    assert parsed.items[0].reason_text == "In the interest of orderly development."


def test_stray_number_line_before_reason_does_not_shift_items():
    body = (
        "1. The development shall be carried out in accordance with the plans.\n"
        "Reason: In the interest of clarity.\n"
        "\n"
        "2. The garage shall not be used for habitable or commercial purposes.\n"
        "3.\n"
        "Reason: In the interest of orderly development.\n"
        "\n"
        "3. The finishes of the garage shall match those of the house.\n"
        "Reason: In the interest of visual amenity."
    )
    parsed = parse_notice(_grant_notice(body, 3), authority="Galway County Council", decision="CONDITIONAL")
    assert parsed.status == "validated"
    assert [i.n for i in parsed.items] == [1, 2, 3]
    assert parsed.items[1].text == "The garage shall not be used for habitable or commercial purposes."
    assert parsed.items[1].reason_text == "In the interest of orderly development."
    assert parsed.items[2].text == "The finishes of the garage shall match those of the house."
    assert parsed.items[2].reason_text == "In the interest of visual amenity."


def test_bare_number_line_followed_by_text_is_still_an_item():
    body = (
        "1.\n"
        "The development shall be carried out in accordance with the plans.\n"
        "Reason: In the interest of clarity.\n"
        "\n"
        "2.\n"
        "Services shall be laid underground.\n"
        "Reason: In the interest of visual amenity."
    )
    parsed = parse_notice(_grant_notice(body, 2), authority="Galway County Council", decision="CONDITIONAL")
    assert parsed.status == "validated"
    assert parsed.items[1].text == "Services shall be laid underground."


def test_bare_number_before_reason_without_later_duplicate_stays_an_item():
    # The bare "2." is the genuine item 2 (no other "2." follows), so the count must hold.
    body = (
        "1. Surface water shall be disposed of on site.\n"
        "2.\n"
        "REASON: In the interest of proper planning.\n"
        "\n"
        "3. The building shall be used for agricultural purposes only.\n"
        "Reason: In the interest of orderly development."
    )
    parsed = parse_notice(_grant_notice(body, 3), authority="Galway County Council", decision="CONDITIONAL")
    assert parsed.status == "validated"
    assert [i.n for i in parsed.items] == [1, 2, 3]
