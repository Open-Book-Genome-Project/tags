"""Public exports for subject classification."""

from __future__ import annotations

from .classifier import SubjectClassifier
from .json_loader import load_mapping, load_set
from .models import ClassificationResult
from .normalization import is_classification_code, is_reading_level, normalize

__all__ = [
    "ClassificationResult",
    "SubjectClassifier",
    "is_classification_code",
    "is_reading_level",
    "load_mapping",
    "load_set",
    "normalize",
]
