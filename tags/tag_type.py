"""
tag_type.py

Core data infrastructure for the tags project:
    - normalize: lowercase + strip + NFC normalization
    - TagMatch: evidence for a classification match (value, source, reason)
    - TagType: profile card for a single tag type with vocabulary, mappings,
      and classification logic
    - build_lookup: builds a flat subject->slug dict from vocabulary and mappings
    - default_classify: default work-level classification

A blueprint: every tag type has these same pieces.
"""

import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional






def normalize(subject: str) -> str:
    """Lowercase, strip, and NFC-normalize a subject string."""
    return unicodedata.normalize('NFC', subject.lower().strip())


@dataclass
class TagMatch:
    """Evidence for a single classification match."""
    value: str
    source: str
    reason: str = "direct mapping"


@dataclass
class TagType:
    """A profile card for one tag type."""
    name: str
    directory: Path
    priority: int = 100
    vocabulary: dict = field(default_factory=dict)
    mappings: dict = field(default_factory=dict)
    classify_fn: Optional[Callable[["TagType", dict], list[TagMatch]]] = None

    def classify(self, work: dict) -> list[TagMatch]:
        """Try classify_fn first, fall through to default_classify."""
        if self.classify_fn:
            return self.classify_fn(self, work)
        return default_classify(self, work)

    def tag_key(self, slug: str) -> str | None:
        """Return the OL Tag key (e.g. 'OL123T') for a slug, or None if not yet created.

        Tag keys are written back into vocabulary.json after OL Tag objects are
        created. Until then, this returns None for all slugs.
        """
        for tag in self.vocabulary.get("tags", []):
            if tag.get("slug") == slug:
                return tag.get("key")
        return None


def build_lookup(tt: TagType) -> dict[str, str]:
    """Build a flat subject->slug dict from a TagType's vocabulary and mappings.

    Sources (later wins):
        1. vocabulary.json - slug, tag name, and aliases
        2. mappings/<type>.json - curated subject-to-slug entries
    """
    lookup: dict[str, str] = {}

    for entry in tt.vocabulary.get("tags", []):
        slug = entry.get("slug", "")
        lookup[normalize(slug)] = slug
        lookup[normalize(entry.get("tag", ""))] = slug
        for alias in entry.get("aliases", []):
            lookup[normalize(alias)] = slug

    for subject, slug in tt.mappings.items():
        lookup[normalize(subject)] = slug

    return lookup


def default_classify(tt: TagType, work: dict) -> list[TagMatch]:
    """Classify a work by matching its subjects against this type's mappings."""
    results = []
    for subject in work.get("subjects", []):
        slug = tt.mappings.get(normalize(subject))
        if slug:
            results.append(TagMatch(value=slug, source=subject))
    return results
