from src.services.llm_client import extract_json


def test_extract_json_plain():
    assert extract_json('{"q": "oranmore"}') == {"q": "oranmore"}


def test_extract_json_with_surrounding_prose():
    text = 'Sure, here is the filter:\n{"q": "oranmore"}\nLet me know if needed.'
    assert extract_json(text) == {"q": "oranmore"}


def test_extract_json_with_code_fence():
    text = '```json\n{"planning_authority": "Galway City Council"}\n```'
    assert extract_json(text) == {"planning_authority": "Galway City Council"}


def test_extract_json_invalid_returns_none():
    assert extract_json("not json at all") is None


def test_extract_json_malformed_braces_returns_none():
    assert extract_json('{"q": "oranmore"') is None
