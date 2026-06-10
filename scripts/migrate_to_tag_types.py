"""
migrate_to_tag_types.py

Migrate from the flat structure to tag_types/<name>/ layout.

Before:
    genres/vocabulary.json
    mappings/genres.json
    tag_types/registry.json

After:
    tag_types/genres/vocabulary.json
    tag_types/genres/mappings.json
    tag_types/registry.json

Run:
    python scripts/migrate_to_tag_types.py

Verify:
    python -c "from tags import load_all; types = load_all(); print([t.name for t in types])"
    tags analyze genres ...  # same coverage as before
"""

import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# Types that have root-level folders with vocabulary.json
TYPES_WITH_VOCAB = [
    "audience", "content_features", "content_formats",
    "content_warnings", "genres", "literary_form",
    "literary_themes", "literary_tropes", "moods", "subgenres",
]

# Types that have mapping files in mappings/
TYPES_WITH_MAPPINGS = [
    "audience", "content_formats", "genres",
    "literary_themes", "literary_tropes", "main_topics", "subgenres",
]

# Types in registry without root vocab — just create directories
EMPTY_TYPES = [
    "main_topics", "sub_topics", "people", "places", "things", "times",
]


def migrate():
    # 1. Migrate types with vocabulary
    for name in TYPES_WITH_VOCAB:
        src = REPO_ROOT / name
        dst = REPO_ROOT / "tag_types" / name
        dst.mkdir(parents=True, exist_ok=True)

        # Move vocabulary files
        for f in ["vocabulary.json", "proposals.md", "README.md", "vocabulary.md"]:
            src_file = src / f
            if src_file.exists():
                shutil.move(str(src_file), str(dst / f))

        # Move mapping if exists
        maps_file = REPO_ROOT / "mappings" / f"{name}.json"
        if maps_file.exists():
            shutil.move(str(maps_file), str(dst / "mappings.json"))

        # Remove old empty directory
        if src.exists() and not list(src.iterdir()):
            src.rmdir()

    # 2. Create empty directories for remaining types
    for name in EMPTY_TYPES:
        dst = REPO_ROOT / "tag_types" / name
        dst.mkdir(parents=True, exist_ok=True)
        # Copy proposals/README if they exist at root level
        src = REPO_ROOT / name
        if src.exists():
            for f in ["proposals.md", "README.md"]:
                src_file = src / f
                if src_file.exists():
                    shutil.move(str(src_file), str(dst / f))
            if src.exists() and not list(src.iterdir()):
                src.rmdir()

    # 3. Move non-standard mapping files
    overrides = ["droppable.json", "people_overrides.json", "places_overrides.json"]
    for name in overrides:
        src_file = REPO_ROOT / "mappings" / name
        if src_file.exists():
            shutil.move(str(src_file), str(REPO_ROOT / "tag_types" / name))

    # 4. Remove old mappings directory if empty
    maps_dir = REPO_ROOT / "mappings"
    if maps_dir.exists() and not list(maps_dir.iterdir()):
        maps_dir.rmdir()

    print("Migration complete. Verify with:")
    print("  python -c \"from tags import load_all; print(len(load_all()))\"")
    print("  git diff --stat")


if __name__ == "__main__":
    migrate()
