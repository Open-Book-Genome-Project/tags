"""Public exports for subject classification."""

from __future__ import annotations

from .engine import TypedTagger
from .json_loader import load_mapping, load_set
from .models import ClassificationResult
from .normalization import is_classification_code, is_reading_level, normalize

__all__ = [
    "ClassificationResult",
    "TypedTagger",
    "is_classification_code",
    "is_reading_level",
    "load_mapping",
    "load_set",
    "normalize",
]
