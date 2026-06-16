"""
normalize_mapping_slugs.py

Convert mapping values from display names to slugs for all tag types.

The data contract in CONTRIBUTING.md says mapping values should be
slugs ("fantasy"), not display names ("Fantasy"). This script reads
each type's vocabulary.json and rewrites its mappings.json so every
value matches the slug form.

Usage:
    python scripts/normalize_mapping_slugs.py

Verify:
    git diff --stat
"""

import json
from pathlib import Path

# Tag types whose mappings need slug values
TYPES = ["genres", "subgenres"]

for name in TYPES:
    # Load vocabulary to build display-name -> slug lookup
    vocab_path = Path(name, "vocabulary.json")
    vocab = json.loads(vocab_path.read_text())
    slug_map = {t["tag"]: t["slug"] for t in vocab["tags"]}

    # Load and convert mapping values
    maps_path = Path("mappings", f"{name}.json")
    maps = json.loads(maps_path.read_text())
    for key, val in maps.items():
        if val in slug_map:
            maps[key] = slug_map[val]

    # Write back
    maps_path.write_text(
        json.dumps(maps, indent=2, ensure_ascii=False) + "\n"
    )
    print(f"  {name}: {len(maps)} entries converted")

print("Done. Run `git diff` to verify only values changed.")
