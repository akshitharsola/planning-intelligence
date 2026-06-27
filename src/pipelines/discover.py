from pathlib import Path

import yaml


def load_region_config(path: Path) -> dict:
    """Load a `config/<county>/<region>.yaml` region config file."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
