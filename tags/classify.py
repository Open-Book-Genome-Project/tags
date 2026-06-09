"""
classify.py

Shared classification helpers for tag types:
    - normalize: lowercase + strip + NFC normalization
    - build_lookup: builds a flat subject -> slug dict from vocabulary and mappings

Used by the CLI (analyze/unmapped) and custom classify.py files.
"""

import unicodedata
from tags.tag_type import TagType

#------------------------------------------------------------------------
# Normalization helpers
#------------------------------------------------------------------------

def normalize(subject: str) -> str:
    """Lowercase, strip, and NFC-normalize a subject string"""
    return unicodedata.normalize('NFC', subject.lower().strip())

#------------------------------------------------------------------------
# Build Lookup
#------------------------------------------------------------------------

def build_lookup(tt: TagType) -> dict[str, str]:
    """
    Build a flat subject -> slug dict from a TagType's vocabulary and mappings.

    Sources (later wins i.e If the same key appears twice, the last one overwrites the first):
        1. vocabulary.json - slug, tag name, and aliases as match terms
        2. mappings/<type>.json - curated subject-to-slug entries
    """
    lookup: dict[str, str] = {}

    # From vocabulary: slug -> slug, tag name -> slug
    for entry in tt.vocabulary.get("tags", []):
        slug = entry.get("slug", "")
        lookup[normalize(slug)] = slug
        # We normalize Display Name as well in case someone searches with it to catch both variants
        lookup[normalize(entry.get("tag", ""))] = slug
        for alias in entry.get("aliases", []):
           lookup[normalize(alias)] = slug

    # From mappings: subject string -> slug
    for subject, slug in tt.mappings.items():
        lookup[normalize(subject)] = slug

    return lookup
