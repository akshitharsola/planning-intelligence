from pathlib import Path

SKILL_PATH = Path(".claude/skills/onboard-council/SKILL.md")
SOURCE_AGENT_PATH = Path(".claude/agents/source-onboarding.md")
PARSER_AGENT_PATH = Path(".claude/agents/parser-dev.md")


def test_skill_file_exists_and_references_both_subagents():
    text = SKILL_PATH.read_text()
    assert "source-onboarding" in text
    assert "parser-dev" in text
    assert "docs/source-inventory.md" in text


def test_source_onboarding_agent_has_frontmatter():
    text = SOURCE_AGENT_PATH.read_text()
    assert text.startswith("---")
    assert "name: source-onboarding" in text
    assert "tools:" in text


def test_parser_dev_agent_has_frontmatter():
    text = PARSER_AGENT_PATH.read_text()
    assert text.startswith("---")
    assert "name: parser-dev" in text
    assert "tools:" in text
