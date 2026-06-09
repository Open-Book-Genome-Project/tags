"""
    tag_type.py

    Defines the core data infrastructure for the tags project:
        - TagType : profile card for a single tag type (genres, subgenres, moods, etc) 
          with vocabulary, mappings, and classification logic.
        - TagMatch: evidence for a classification match (value, source, reason)

    It's like a blueprint or template that says "Every tag type should have these pieces of information".
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

@dataclass
class TagMatch:
    """Evidence for a single classification match."""
    value: str      # canonical slug, e.g "fantasy"
    source: str     # raw input that triggered it, e.g "epic fantasy"
    reason: str = "direct mapping"

@dataclass
class TagType:
    """A profile card for one tag type."""
    name: str
    directory: Path
    priority: int = 100
    vocabulary: dict =  field(default_factory=dict)
    mappings: dict = field(default_factory=dict)
    classify_fn: Optional[Callable[["TagType", dict], list[TagMatch]]] = None

    def classify(self, work: dict) -> list[TagMatch]:
         """Try classify_fn first, fall through to default_classify."""
         if self.classify_fn:
             return self.classify_fn(self, work)
         return default_classify(self, work)
    
def default_classify(tt: TagType, work: dict) -> list[TagMatch]:
    """"""
    results = []
    for subject in work.get("subjects", []):
        slug = tt.mappings.get(subject.lower().strip())
        if slug:
            results.append(TagMatch(value=slug, source=subject))
    return results
