"""
backfill_genre_refs.py - Populate the `genre` field on the subgenre Tags.

Reads parent genre mappings from the subgenre vocabularly,
looks up parent genre Tag keys on OL, and wrtes the genre
reference to each subgenre Tag object.

Prerequisites:
    - PR adding the 'genre' property to /type/tag must be merged
    - ~/.config/ol.ini must have credentials

Usage:
    python scripts/backfill_genre_refs.py --dry-run    # preview only
    python scripts/backfill_genre_refs.py              # write changes
"""

import json
import sys
import logging
import requests
import argparse
from pathlib import Path

# sys.path.insert lets us import from scripts/ even when running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from tags.utils import get_ol_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load vocabularry mappings
# ---------------------------------------------------------------------------
def load_subgenre_parents(vocab_path: str) -> dict[str, list[str]]:
    """
    Read tag_types/subgenres/vcabulary.json and extract parent genre names for each subgenre Tag.

    Returns:
        dict mappping subgenre Tag key to list of parent genre names.
        Example: {"/tags/OL268T": ["Sci-Fi"], ["/tags/OL252T"; ["Horror", "Romance"]}
    """
    with open(vocab_path) as f:
        vocab = json.load(f)

    # Each subgenre entry has a "key" and "parent_genres" list
    mappings = {}
    for tag in vocab["tags"]:
        key = tag["key"]            # e.g "/tags/OL268T"
        parents = tag.get("parent_genres", [])      # e.g ["Sci-fi"]
        if parents:
            mappings[key] = parents

    logger.info(f"Loaded {len(mappings)} subgenre-parent mappings from vocabulary")
    return mappings


# ---------------------------------------------------------------------------
# Look up parent genre Tag kes on OL
# ---------------------------------------------------------------------------
# def get_genre_key_map_versionA(ol) -> dict[str, str]:
#     """
#     Query OL for all genre Tags and build a name-key mapping.

#     Uses the OL search API to find all tags with tag_type=genres.
#     Returns a dict mapping lowercase genre name to its Tag key.

#     Example: {"sci-fi": "/tags/OL272T", "horror": "/tags/OL171T"}

#     Note: Will only work when genre tags get indexed in solr
#     """
#     genre_map = {}
#     offset = 0
#     limit = 100

#     while True:
#         # Query OL search API for genre Tags
#         url = f"https://openlibrary.org/search.json?type=/type/tag&tag_type=genres&limit={limit}&offset={offset}"
#         resp = requests.get(url)
#         resp.raise_for_status()
#         data = resp.json()

#         docs = data.get("docs", [])
#         if not docs:
#             break

#         for doc in docs:
#             name = doc.get("name", "")
#             key = doc.get("key", "")
#             if name and key:
#                 # Store lowercase name -> key mapping for case-insentitive lookup
#                 genre_map[name.lower()] = key

#         offset += limit

#     logger.info(f"Found {len(genre_map)} genre Tags on OL")
#     return genre_map


def get_genre_key_map() -> dict[str, str]:
    """
    Read tag_types/genres/vocabulary.json to build name->key mapping.
    No OL API call needed - the vocabulary already has the keys.
    """
    vocab_path = Path(__file__).parent.parent / "tag_types" / "genres" / "vocabulary.json"
    with open(vocab_path) as f:
        vocab = json.load(f)

        genre_map = {}
        for tag in vocab["tags"]:
            name = tag["tag"]       # e.g. "Horror"
            key = tag["key"]        # e.g. "/tags/OL171T"
            genre_map[name.lower()] = key

        logger.info(f"Loaded {len(genre_map)} genre mappings from vocabulary")
        return genre_map
            

# ---------------------------------------------------------------------------
# Extract OLID from tag key
# ---------------------------------------------------------------------------
def extract_olid(tag_key: str) -> str:
    """
    Extract the OLID from a Tag key.
    Example: "/tags/OL268T"
    """
    return tag_key.split("/")[-1]


# ---------------------------------------------------------------------------
# Main backfill logic
# ---------------------------------------------------------------------------
def backfill_genre_refs(dry_run: bool = True) -> None:
    """
    For each subgenre Tag:
        1. Get parent genre name(s) from vocabulary
        2. Look up parent genre Tag key(s) from OL
        3. Write genre refrence(s) to the subgenre Tag
    
    Uses olclients's Tag.save() method for individual updates bbecause we're modifying existing Tags, 
    not creating new ones, so save() is the idiomatic olclient pattern for individual updates.

    Args:
        dry_run: if True, preview changes without writing to OL.
    """
    # Step 1: Load subgenre -> parent genre name mappings from vocabulary
    vocab_path = Path(__file__).parent.parent / "tag_types" / "subgenres" / "vocabulary.json"
    subgenre_parents = load_subgenre_parents(str(vocab_path))

    # Step 2: Get the genre name -> key map from vocabulary
    genre_map = get_genre_key_map()

    # Connect to OL only when writing (not needed for dry-run)
    ol = get_ol_session() if not dry_run else None

    # Step 3: Process each subgenre Tag
    updated = 0
    errors = 0

    for subgenre_key, parent_names in subgenre_parents.items():
        # Look up the parent genre Tag keys (lowercase match)
        genre_refs = []
        missing = []

        for name in parent_names:
            key = genre_map.get(name.lower())
            if key:
                genre_refs.append({"key": key})
            else:
                missing.append(name)

        # Log warning for any parent genres not found on OL
        if missing:
            logger.warning(f"{subgenre_key}: parent genres not found on OL: {missing}")

        # Skip if no valid genre refrences found
        if not genre_refs:
            logger.warning(f"{subgenre_key}: no valid genre refrences, skipping")
            errors += 1
            continue
        if dry_run:
            # Preview mode: show what would be written
            logger.info(f"[DRY RUN] {subgenre_key}: genre = {genre_refs}")
            updated += 1
            continue

        # Fetch the subgenre Tag object from OL using olclient
        try:
            olid = extract_olid(subgenre_key)
            tag = ol.Tag.get(olid)
        except Exception as e:
            logger.error(f"Error fetching {subgenre_key}: {e}")
            errors += 1
            continue

        # Set the genre field on the Tag object
        tag.genre = genre_refs

        # Save nback to OL using olclient's Tag.save() method
        try:
            tag.save(comment="backfill genre refs from vocabulary")
            updated +=1
            logger.info(f"Updated {subgenre_key}: genre = {genre_refs}")
        except Exception as e:
            logger.error(f"Error saving {subgenre_key}: {e}")
            errors += 1

    # Summary
    logger.info(f"Done: {updated} subgenre Tags updated, {errors} errors")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    """
    --dry-run Preview changes without writing to OL.
    """
    parser = argparse.ArgumentParser(description="Backfill genre refs on subgenre Tags")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    backfill_genre_refs(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
