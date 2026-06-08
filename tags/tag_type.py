"""
tag_type.py

Defines the TagType dataclass - the core data structure that represents
a single tag type (genres, subgenres, moods, etc) and its classification logic.

It's like a blueprint or template that says "Every tag type should have these pieces of information".
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

# A Classifier function receives a subject string and the TagType instance,
# and returns a canonical slug if matched, or None to fall through to default.
Classifier = Callable[[str, "TagType"], Optional[str]]

@dataclass
class TagType:
    """A profile card for one tag type."""

    name: str
    directory: Path
    priority: int = 100
    vocabulary: dict = field(default_factory=dict)
    mappings: dict = field(default_factory=dict)
    classify_fn: Optional[Classifier] = None

    def classify(self, subject: str) -> Optional[str]:
        """Try classify_fn first, fall through to default_classify."""
        if self.classify_fn:
            result = self.classify_fn(subject, self)
            if result is not None:
                return result
        from tags.classify import default_classify
        return default_classify(subject, self)
