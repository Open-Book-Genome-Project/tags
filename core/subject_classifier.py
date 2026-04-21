"""Reusable classification core for subject migration."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from core.run_state import RunState

DEFAULT_OUTPUT_TYPES = (
    "literary_form",
    "audience",
    "genres",
    "subgenres",
    "content_formats",
    "moods",
    "literary_themes",
    "literary_tropes",
    "main_topics",
    "sub_topics",
    "people",
    "places",
    "times",
    "things",
    "reading_level",
    "classification_codes",
    "unmapped",
)


class SubjectClassifier:
    """Public orchestration layer for work-level subject classification."""

    def __init__(
        self,
        rule_packs: Iterable[Any],
        output_types: Iterable[str] | None = None,
    ) -> None:
        self.rule_packs = list(rule_packs)
        self.output_types = tuple(output_types or DEFAULT_OUTPUT_TYPES)

    def classify_work(self, work: Mapping[str, Any]) -> dict[str, list[str]]:
        """Run the enabled rule packs against a normalized work object."""
        state = RunState(
            work=work,
            result={tag_type: [] for tag_type in self.output_types},
            remaining_subjects=list(work.get("subjects", [])),
        )
        for pack in self.rule_packs:
            pack.apply(state)
        return state.result
