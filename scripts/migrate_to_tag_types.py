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

# Types in registry without root vocab — just need directories
EMPTY_TYPES = [
    "main_topics", "sub_topics", "people", "places", "things", "times",
]

# Override files to move into specific type directories
OVERRIDES = {
    "people_overrides.json": ("people", "people_overrides.json"),
    "places_overrides.json": ("places", "places_overrides.json"),
    "droppable.json": None,  # stays at tag_types/ root level
}


def migrate():
    # 1. Migrate types with vocabulary (and optionally mappings)
    for name in TYPES_WITH_VOCAB:
        src = REPO_ROOT / name
        dst = REPO_ROOT / "tag_types" / name
        dst.mkdir(parents=True, exist_ok=True)

        for f in ["vocabulary.json", "proposals.md", "README.md", "vocabulary.md"]:
            src_file = src / f
            if src_file.exists():
                shutil.move(str(src_file), str(dst / f))

        maps_file = REPO_ROOT / "mappings" / f"{name}.json"
        if maps_file.exists():
            shutil.move(str(maps_file), str(dst / "mappings.json"))

        if src.exists() and not list(src.iterdir()):
            src.rmdir()

    # 2. Handle types with mappings but no root vocab folder
    for name in TYPES_WITH_MAPPINGS:
        if name not in TYPES_WITH_VOCAB:
            dst = REPO_ROOT / "tag_types" / name
            dst.mkdir(parents=True, exist_ok=True)
            maps_file = REPO_ROOT / "mappings" / f"{name}.json"
            if maps_file.exists():
                shutil.move(str(maps_file), str(dst / "mappings.json"))

    # 3. Create directories for remaining empty types
    for name in EMPTY_TYPES:
        if name in TYPES_WITH_VOCAB or name in TYPES_WITH_MAPPINGS:
            continue
        dst = REPO_ROOT / "tag_types" / name
        dst.mkdir(parents=True, exist_ok=True)
        src = REPO_ROOT / name
        if src.exists():
            for f in ["proposals.md", "README.md"]:
                src_file = src / f
                if src_file.exists():
                    shutil.move(str(src_file), str(dst / f))
            if src.exists() and not list(src.iterdir()):
                src.rmdir()

    # 4. Move override files to their proper tag_types subdirectories
    for filename, dest in OVERRIDES.items():
        if dest is None:
            continue
        subdir, new_name = dest
        dst_file = REPO_ROOT / "tag_types" / subdir / new_name

        # Already in place with correct name?
        if dst_file.exists():
            continue

        # Check for wrong-named file (overrides.json from a previous run)
        wrong_name = REPO_ROOT / "tag_types" / subdir / "overrides.json"
        if wrong_name.exists():
            shutil.move(str(wrong_name), str(dst_file))
            continue

        # Check old locations
        for src_candidate in [
            REPO_ROOT / "mappings" / filename,
            REPO_ROOT / "tag_types" / filename,
        ]:
            if src_candidate.exists():
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src_candidate), str(dst_file))
                break

    # Handle droppable.json (stays at tag_types/ root)
    for src_candidate in [
        REPO_ROOT / "mappings" / "droppable.json",
        REPO_ROOT / "tag_types" / "droppable.json",
    ]:
        if src_candidate.exists() and src_candidate.parent.name != "tag_types":
            shutil.move(str(src_candidate), str(REPO_ROOT / "tag_types" / "droppable.json"))
            break

    # 5. Remove old mappings directory if empty
    maps_dir = REPO_ROOT / "mappings"
    if maps_dir.exists() and not list(maps_dir.iterdir()):
        maps_dir.rmdir()

    print("Migration complete.")
    print("Verify with:")
    print("  python -c \"from tags import load_all; print(len(load_all()))\"")
    print("  git status")


if __name__ == "__main__":
    migrate()
