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
        """Return only the proposed tags for compatibility callers."""
        return self.classify_work_report(work)["proposed_tags"]

    def classify_work_report(self, work: Mapping[str, Any]) -> dict[str, Any]:
        """Run the enabled rule packs against a normalized work object."""
        original_subjects = list(work.get("subjects", []))
        state = RunState(
            work=work,
            result={tag_type: [] for tag_type in self.output_types},
            original_subjects=original_subjects,
            remaining_subjects=list(original_subjects),
        )
        for pack in self.rule_packs:
            pack.apply(state)
        return {
            "proposed_tags": state.result,
            "subject_proposal": {
                "original": state.original_subjects,
                "removed": state.removed_subjects,
                "remaining": state.remaining_subjects,
            },
            "subject_matches": state.subject_matches,
        }
