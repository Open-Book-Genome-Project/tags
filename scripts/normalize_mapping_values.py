"""
normalize_mapping_values.py

Convert mapping values from display names to slugs for all tag types.

The data contract in CONTRIBUTING.md says mapping values should be
slugs ("fantasy"), not display names ("Fantasy"). This script reads
each type's vocabulary.json and rewrites its mappings.json so every
value matches the slug form.

For types WITH vocabulary.json: builds a display-name -> slug lookup.
For open types WITHOUT vocabulary.json: lowercases values in-place.

Usage:
    python scripts/normalize_mapping_values.py [--dry-run]

Verify:
    git diff --stat
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
TAG_TYPES_DIR = REPO_ROOT / "tag_types"
DRY_RUN = "--dry-run" in sys.argv


def build_slug_lookup(vocab: dict) -> dict[str, str]:
    """Build a case-insensitive display-name -> slug mapping from vocabulary.json."""
    lookup: dict[str, str] = {}
    for tag in vocab.get("tags", []):
        slug = tag["slug"]
        # Register slug itself, display name, and all aliases
        lookup[slug.lower()] = slug
        lookup[tag["tag"].lower()] = slug
        for alias in tag.get("aliases", []):
            lookup[alias.lower()] = slug
    return lookup


def normalize_value(val: str, lookup: dict[str, str]) -> str:
    """Convert a mapping value to its canonical slug, or lowercase if unknown."""
    if val.lower() in lookup:
        return lookup[val.lower()]
    # Fallback: lowercase only (for open types or unknown values)
    return val.lower()


for type_dir in sorted(TAG_TYPES_DIR.iterdir()):
    if not type_dir.is_dir():
        continue

    maps_path = type_dir / "mappings.json"
    if not maps_path.exists():
        continue

    vocab_path = type_dir / "vocabulary.json"
    lookup: dict[str, str] = {}
    if vocab_path.exists():
        vocab = json.loads(vocab_path.read_text())
        lookup = build_slug_lookup(vocab)

    maps = json.loads(maps_path.read_text())
    updated = {k: normalize_value(v, lookup) for k, v in maps.items()}
    changed = sum(1 for k in maps if maps[k] != updated[k])

    if changed:
        print(f"  {type_dir.name}: {changed} values updated")
        if not DRY_RUN:
            maps_path.write_text(json.dumps(updated, indent=2, ensure_ascii=False) + "\n")
    else:
        print(f"  {type_dir.name}: already clean")

if DRY_RUN:
    print("\nDry run — no files written.")
else:
    print("\nDone. Run `git diff` to verify only values changed.")
