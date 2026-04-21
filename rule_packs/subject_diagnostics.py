"""Rule pack for dropped, reading-level, classification, and unmapped subjects."""

from __future__ import annotations

from core.run_state import RunState
from rule_engine.base import RulePack
from rule_engine.normalization import (
    is_classification_code,
    is_reading_level,
    normalize,
)


class SubjectDiagnosticsPack(RulePack):
    name = "subject_diagnostics"
    output_types = ("reading_level", "classification_codes", "unmapped")

    def __init__(self, droppable: set[str] | None = None) -> None:
        self.droppable = set(droppable or ())

    def apply(self, state: RunState) -> None:
        for raw in state.remaining_subjects:
            key = normalize(raw)
            if key in self.droppable:
                continue

            if is_reading_level(raw):
                value = raw.strip()
                if value:
                    state.add("reading_level", value)
                continue

            if is_classification_code(raw):
                value = raw.strip()
                if value:
                    state.add("classification_codes", value)
                continue

            value = raw.strip()
            if value:
                state.add("unmapped", value)
