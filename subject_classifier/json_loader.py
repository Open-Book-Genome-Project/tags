"""JSON resource loaders for migration mappings."""

from __future__ import annotations

import json
from pathlib import Path

from .normalization import normalize

REPO_ROOT = Path(__file__).resolve().parents[1]
MAPPINGS_DIR = REPO_ROOT / "scripts" / "mappings"


def load_mapping(name: str) -> dict[str, str]:
    """Load a JSON mapping file from scripts/mappings/."""
    path = MAPPINGS_DIR / f"{name}.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def load_set(name: str) -> set[str]:
    """Load a JSON list file as a normalized set."""
    path = MAPPINGS_DIR / f"{name}.json"
    if not path.exists():
        return set()
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        return {normalize(str(item)) for item in data}
    return {normalize(str(item)) for item in data.keys()}
