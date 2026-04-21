"""Compatibility wrapper for migration classifier assembly."""

from __future__ import annotations

from core.classifier_assembler import (
    build_subject_classifier,
    resolve_pack_names,
)
from core.pack_registry import AVAILABLE_PACK_NAMES, PACK_FACTORIES, PACK_PRESETS

__all__ = [
    "AVAILABLE_PACK_NAMES",
    "PACK_FACTORIES",
    "PACK_PRESETS",
    "build_subject_classifier",
    "resolve_pack_names",
]
