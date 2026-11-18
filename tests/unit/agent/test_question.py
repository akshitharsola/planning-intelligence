import pytest

from src.agent.llm import make_ollama_interpreter, merge_llm_filters
from src.agent.question import CITY, COUNTY, parse_question


def test_long_number_is_a_reference():
    q = parse_question("Why was application 2660494 refused?")
    assert q.refs == ["2660494"]
    assert q.decision == "REFUSED" and q.wants_reasons


def test_year_is_not_a_reference_unless_marked():
    assert parse_question("refusals in 2025").refs == []
    assert parse_question("refusals in 2025").year == 2025
    assert parse_question("application 2021").refs == ["2021"]
    assert parse_question("status of ref 268").refs == ["268"]


def test_council_words():
    assert parse_question("city application 22179").authority == CITY
    assert parse_question("County application 2447").authority == COUNTY
    assert parse_question("application 2447").authority is None


def test_place_and_topic_groups():
    q = parse_question("Conditions about flooding in Oughterard")
    assert q.place == "Oughterard"
    assert q.decision == "CONDITIONAL" and q.wants_conditions
    assert q.topic_terms == ["flooding"]
    assert q.topic_groups == [["flood", "flooding"]]


def test_filler_words_are_not_topics():
    q = parse_question("how many refusals mention road safety")
    assert q.wants_count
    assert q.topic_terms == ["road", "safety"]


def test_help():
    assert parse_question("help").is_help


def test_llm_merge_only_fills_gaps_and_validates():
    q = parse_question("anything refused near the sea in 2026")
    merged = merge_llm_filters(q, {"decision": "CONDITIONAL", "year": 1999, "place": "Spiddal; DROP TABLE",
                                   "council": "county", "topic": ["coastal", "x", 5], "count": True})
    assert merged.decision == "REFUSED"          # rules win
    assert merged.year == 2026                   # rules win
    assert merged.place is None                  # invalid place rejected
    assert merged.authority == COUNTY
    assert merged.wants_count is True


def test_llm_merge_adds_topic_when_rules_found_none():
    q = parse_question("refused 2026")
    merged = merge_llm_filters(q, {"topic": ["Wastewater"]})
    assert merged.topic_terms == ["wastewater"]
    assert "septic" in merged.topic_groups[0]


def test_ollama_interpreter_uses_json_response():
    calls = {}

    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"response": '{"decision": "REFUSED", "place": "Clifden", "topic": [], "count": false}'}

    def fake_post(url, json=None, timeout=None):
        calls["url"], calls["body"] = url, json
        return Resp()

    interp = make_ollama_interpreter(base_url="http://ollama.test", model="m", post=fake_post)
    q = interp("what got turned down out west", parse_question("what got turned down out west"))
    assert calls["url"] == "http://ollama.test/api/generate"
    assert calls["body"]["format"] == "json"
    assert q.decision == "REFUSED" and q.place == "Clifden"


def test_month_is_not_a_place():
    q = parse_question("Tell me reasons for the applications refused in March in Galway county")
    assert q.month == 3 and q.place is None
    assert q.authority == COUNTY and q.decision == "REFUSED" and q.asks_item_text


@pytest.mark.parametrize("text,month", [("refusals in sept", 9), ("granted in May 2026", 5), ("refused in dec", 12)])
def test_month_forms(text, month):
    assert parse_question(text).month == month


def test_may_as_a_verb_is_not_a_month():
    q = parse_question("what may be refused in Tuam")
    assert q.month is None and q.place == "Tuam"
