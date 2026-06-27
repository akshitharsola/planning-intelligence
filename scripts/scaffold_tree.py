# scripts/scaffold_tree.py — run once: `python3 scripts/scaffold_tree.py`
# Cross-platform (macOS/Linux/Windows) replacement for `mkdir -p` + `touch`.
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DIRS = [
    "config/galway",
    "data/galway/city/temp",
    "data/galway/county/temp",
    "src/core/models",
    "src/core/db/migrations",
    "src/core/schemas",
    "src/core/normalization",
    "src/core/lifecycle",
    "src/core/geo",
    "src/parsers/pdf_lines",
    "src/parsers/pdf_text_fallback",
    "src/parsers/docx_state_machine",
    "src/parsers/pdf_ocr",
    "src/sources/base",
    "src/sources/galway/city",
    "src/sources/galway/county",
    "src/pipelines",
    "src/markets/galway",
    "src/services",
    "src/monitoring",
    "tests/fixtures",
    "tests/unit/parsers",
    "tests/integration",
    "tests/regression",
    ".claude/skills/onboard-council",
    ".claude/agents",
]

INIT_FILES = [
    "src/__init__.py",
    "src/core/__init__.py",
    "src/core/models/__init__.py",
    "src/core/db/__init__.py",
    "src/core/schemas/__init__.py",
    "src/core/normalization/__init__.py",
    "src/core/lifecycle/__init__.py",
    "src/core/geo/__init__.py",
    "src/parsers/__init__.py",
    "src/parsers/pdf_lines/__init__.py",
    "src/parsers/pdf_text_fallback/__init__.py",
    "src/parsers/docx_state_machine/__init__.py",
    "src/parsers/pdf_ocr/__init__.py",
    "src/sources/__init__.py",
    "src/sources/base/__init__.py",
    "src/sources/galway/__init__.py",
    "src/sources/galway/city/__init__.py",
    "src/sources/galway/county/__init__.py",
    "src/pipelines/__init__.py",
    "src/markets/__init__.py",
    "src/markets/galway/__init__.py",
    "src/services/__init__.py",
    "src/monitoring/__init__.py",
    "config/__init__.py",
]


def main() -> None:
    for rel in DIRS:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)

    for rel in INIT_FILES:
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)

    for tests_dir in (ROOT / "tests").rglob("*"):
        if tests_dir.is_dir():
            (tests_dir / ".gitkeep").touch(exist_ok=True)

    for temp_dir in (ROOT / "data").rglob("temp"):
        if temp_dir.is_dir():
            (temp_dir / ".gitkeep").touch(exist_ok=True)

    print("Scaffold tree created.")


if __name__ == "__main__":
    main()
