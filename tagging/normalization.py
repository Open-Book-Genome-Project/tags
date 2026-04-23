"""Normalization and classification helpers."""

from __future__ import annotations

import re

READING_LEVEL_RE = re.compile(
    r"reading level.grade\s*\d+|grade\s*\d+|rl\s*\d+", re.IGNORECASE
)
CLASSIFICATION_RE = re.compile(
    r"^[0-9]{3}(\.[0-9]+)?$|^[a-z]{1,3}\s*[0-9]+|^pr[0-9]", re.IGNORECASE
)


def normalize(value: str) -> str:
    """Lowercase and strip a subject string for mapping lookup."""
    return value.lower().strip()


def is_reading_level(value: str) -> bool:
    return bool(READING_LEVEL_RE.search(value))


def is_classification_code(value: str) -> bool:
    return bool(CLASSIFICATION_RE.match(value.strip()))
