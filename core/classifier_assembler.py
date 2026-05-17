"""Assembly helpers for building migration classifiers."""

from __future__ import annotations

from collections.abc import Iterable

from core.json_loader import load_set
from core.pack_registry import (
    AVAILABLE_PACK_NAMES,
    PACK_FACTORIES,
    PACK_PRESETS,
)
from core.subject_classifier import SubjectClassifier


def resolve_pack_names(enabled_packs: Iterable[str] | None) -> list[str]:
    """Expand presets into concrete stable pack names."""
    selected = list(enabled_packs or [])
    expanded: list[str] = []
    for name in selected:
        if name in PACK_PRESETS:
            expanded.extend(PACK_PRESETS[name])
            continue
        expanded.append(name)
    return expanded


def build_subject_classifier(
    enabled_packs: Iterable[str] | None = None,
) -> SubjectClassifier:
    """Build the migration classifier from an explicit pack-name list."""
    selected = resolve_pack_names(enabled_packs)
    missing = [name for name in selected if name not in PACK_FACTORIES]
    if missing:
        available = ", ".join(AVAILABLE_PACK_NAMES)
        missing_display = ", ".join(sorted(missing))
        raise ValueError(
            f"Unknown rule pack(s): {missing_display}. Available: {available}"
        )

    return SubjectClassifier(rule_packs=[PACK_FACTORIES[name]() for name in selected])
