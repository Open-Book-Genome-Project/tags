"""JSON resource loaders for migration assembly."""

from __future__ import annotations

import json
from pathlib import Path

from rule_engine.normalization import normalize

REPO_ROOT = Path(__file__).resolve().parent.parent
MAPPINGS_DIR = REPO_ROOT / "resources" / "mappings"


def load_mapping(name: str) -> dict[str, str]:
    """Load a JSON mapping file from resources/mappings/."""
    path = MAPPINGS_DIR / f"{name}.json"
    if not path.exists():
        return {}
    with open(path) as handle:
        return json.load(handle)


def load_set(name: str) -> set[str]:
    """Load a JSON list file as a normalized set."""
    path = MAPPINGS_DIR / f"{name}.json"
    if not path.exists():
        return set()
    with open(path) as handle:
        data = json.load(handle)
    if isinstance(data, list):
        return {normalize(item) for item in data}
    return {normalize(item) for item in data.keys()}
