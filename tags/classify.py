"""
classify.py

Default classification logic for TagType instances.
Most tag types (genres, subgenres, moods, etc.) use this 
function rather than writing custom classify.py files.
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
# Default classifier
#------------------------------------------------------------------------

def default_classify(subject: str, tt: TagType) -> str | None:
    """
    Look up a subject string in the tag type's mappings.
    Returns the canonical slug if found, None otherwise.
    Subclasses can call this as a fallback after custom logic.
    """
    key = normalize(subject)
    return tt.mappings.get(key)
