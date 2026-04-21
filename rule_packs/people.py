"""Rule pack for subject_people."""

from __future__ import annotations

from collections.abc import Mapping

from core.json_loader import load_mapping
from core.run_state import RunState
from rule_engine.base import RulePack
from rules import OverrideRule


class PeoplePack(RulePack):
    name = "people"
    output_types = ("people",)

    def __init__(self, overrides: Mapping[str, str] | None = None) -> None:
        self.rule = OverrideRule(overrides)

    def apply(self, state: RunState) -> None:
        for raw in state.work.get("subject_people", []):
            value = self.rule.apply(raw)
            if value is not None:
                state.add("people", value)

    @classmethod
    def default(cls) -> "PeoplePack":
        return cls(overrides=load_mapping("people_overrides"))
