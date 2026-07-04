"""
migrate_work.py - Classify a Work's subjects into typed Tag keys.

Usage:
    python scripts/migrate_work.py --work OL82563W --dry-run
"""

import json
import sys
from pathlib import Path

from tags.utils import slug_to_tag_key

REPO_ROOT = Path(__file__).parent.parent
TAG_TYPES_DIR = REPO_ROOT / "tag_types"

# Types that get Tag keys in typed work fields
MIGRATABLE_TYPES = [
    "genres", "subgenres", "audience", "moods", "content_formats",
    "literary_themes", "literary_tropes", "literary_form",
    "content_warnings", "content_features",
]

class WorkMigrator:
    """Classifies a Work's subjects into typed Tag keys."""

    def __init__(self):
        # Loads mappings from tag_types/<name>/mappings.json for all types
        self.mappings = {}
        for t in MIGRATABLE_TYPES:
            self.mappings[t] = self._load_mappings(t)
    
    def _load_mappings(self, type_name: str) -> dict[str, str]:
        """Load normalized subject-slug mappings from tag_types/<name>/mappings.json"""
        path = TAG_TYPES_DIR / type_name / "mappings.json"
        if not path.exists():
            return {}
        raw = json.loads(path.read_text())
        return {k.lower().strip(): v for k, v in raw.items()}
    
    def classify_subject(self, subject: str) -> tuple[str, str] | None:
        """Given a subject string, return (type_name, slug) or None."""
        key = subject.lower().strip()
        for tag_type in MIGRATABLE_TYPES:
            if key in self.mappings.get(tag_type, {}):
                return (tag_type, self.mappings[tag_type][key])
        return None
    
    def migrate(self, work: dict) -> dict[str, list[str]]:
        """
        Given a Work dict from OL API, return typed Tag keys.
        Example: {"genres": ["/tags/OL179T"], "subgenres": ["/tags/OL272T"]}
        """
        result = {t: [] for t in MIGRATABLE_TYPES}
        for subject in work.get("subjects", []):
            classified = self.classify_subject(subject)
            if classified:
                tag_type, slug = classified
                tag_key = slug_to_tag_key(tag_type, slug)
                if tag_key and tag_key not in result[tag_type]:
                    result[tag_type].append(tag_key)
        return {k: v for k, v in result.items() if v}

if __name__ ==  "__main__":
    import argparse
    import requests

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Classify a Work's subjects into typed Tag keys."
    )
    parser.add_argument("--work", required=True, help="OL Work ID (e.g OL82563W)")
    parser.add_argument("--dry-run", action="store_true", help="Print results, don't write")
    args = parser.parse_args()

    # Remove /works/ prefix if present, then fetch work JSON from Open Library
    work_id = args.work.replace("works/", "")
    resp = requests.get(f"http://openlibrary.org/works/{work_id}.json")
    resp.raise_for_status()
    work = resp.json()

    # Just to help us confirm the title of the book
    title = work.get("title", "Unknown")

    # Classify subjects and convert slugs to Tag keys
    migrator = WorkMigrator()
    result = migrator.migrate(work)

    if args.dry_run:
        # Print results in a human friendly format
        print(f"\n=== {work_id}: {title} ===") # Added the title here just to confirm the book name
        for tag_type, keys in result.items():
            print(f"  {tag_type}:")
            for k in keys:
                print(f"   - {k}")
    else:
        # Output raw JSON (for piping to other tools)
        print(json.dumps(result, indent=2))
