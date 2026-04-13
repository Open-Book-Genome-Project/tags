"""
Loads vocabulary.json files from each type directory into dicts
that the DB seeder can ingest.

The vocabulary.json files are the canonical source of truth.
This loader discovers them automatically — add a new type directory
with a vocabulary.json and it will be picked up on next startup.
"""

import json
from pathlib import Path

# Types whose directories live one level above this api/ package
REPO_ROOT = Path(__file__).parent.parent

# Types that have open/unstructured vocabularies (no vocabulary.json).
# These are still registered as types but have no pre-seeded tags.
OPEN_TYPES = {
    "main_topics": {
        "type": "main_topics",
        "label": "Main Topics",
        "description": "Primary concepts or academic subject matter the work is substantially about.",
        "controlled": False,
        "tags": [],
    },
    "sub_topics": {
        "type": "sub_topics",
        "label": "Sub Topics",
        "description": "Secondary or supporting concepts that populate the world of the work.",
        "controlled": False,
        "tags": [],
    },
    "things": {
        "type": "things",
        "label": "Things",
        "description": "Tangible objects, creatures, or concrete nouns physically present in the text.",
        "controlled": False,
        "tags": [],
    },
    "people": {
        "type": "people",
        "label": "People",
        "description": "Characters, real persons, or fictional individuals named and present in the work.",
        "controlled": False,
        "tags": [],
    },
    "places": {
        "type": "places",
        "label": "Places",
        "description": "Geographic locations, specific settings, and meaningful places in the work.",
        "controlled": False,
        "tags": [],
    },
    "times": {
        "type": "times",
        "label": "Times",
        "description": "Specific eras, time periods, or historical epochs during which the work is set.",
        "controlled": False,
        "tags": [],
    },
}


def load_vocabulary(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def load_all_vocabularies() -> list[dict]:
    """
    Discover and load all vocabulary.json files from type directories.
    Returns a list of vocabulary dicts, ready for DB.seed().
    """
    vocabularies = []

    for type_dir in sorted(REPO_ROOT.iterdir()):
        if not type_dir.is_dir():
            continue
        if type_dir.name.startswith(".") or type_dir.name in ("api", "scripts"):
            continue

        vocab_file = type_dir / "vocabulary.json"
        if vocab_file.exists():
            try:
                vocab = load_vocabulary(vocab_file)
                # Ensure the type field matches directory name
                if "type" not in vocab:
                    vocab["type"] = type_dir.name
                vocabularies.append(vocab)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: could not load {vocab_file}: {e}")

    # Register open types that have no vocabulary.json yet
    loaded_types = {v["type"] for v in vocabularies}
    for type_name, meta in OPEN_TYPES.items():
        if type_name not in loaded_types:
            vocabularies.append(meta)

    return vocabularies
