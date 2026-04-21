"""Shared runtime state for sequential subject classification."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RunState:
    """Mutable state shared by packs during sequential execution."""

    work: Mapping[str, Any]
    result: dict[str, list[str]]
    original_subjects: list[str] = field(default_factory=list)
    remaining_subjects: list[str] = field(default_factory=list)
    removed_subjects: list[str] = field(default_factory=list)
    retained_matched_subjects: set[str] = field(default_factory=set)
    subject_matches: list[dict[str, str]] = field(default_factory=list)

    def add(self, output_type: str, value: str) -> None:
        if output_type not in self.result:
            self.result[output_type] = []
        if value not in self.result[output_type]:
            self.result[output_type].append(value)

    def record_subject_match(
        self,
        raw: str,
        output_type: str,
        value: str,
        action: str,
    ) -> None:
        self.subject_matches.append(
            {
                "subject": raw,
                "output_type": output_type,
                "value": value,
                "action": action,
            }
        )

    def record_removed_subject(self, raw: str) -> None:
        self.removed_subjects.append(raw)

    def record_retained_subject(self, raw: str) -> None:
        self.retained_matched_subjects.add(raw.lower().strip())
