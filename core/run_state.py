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
    remaining_subjects: list[str] = field(default_factory=list)

    def add(self, output_type: str, value: str) -> None:
        if output_type not in self.result:
            self.result[output_type] = []
        if value not in self.result[output_type]:
            self.result[output_type].append(value)
