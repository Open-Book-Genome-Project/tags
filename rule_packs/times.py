"""Rule pack for subject_times."""

from __future__ import annotations

from core.run_state import RunState
from rule_engine.base import RulePack
from rules import PassthroughRule


class TimesPack(RulePack):
    name = "times"
    output_types = ("times",)

    def __init__(self) -> None:
        self.rule = PassthroughRule()

    def apply(self, state: RunState) -> None:
        for raw in state.work.get("subject_times", []):
            value = self.rule.apply(raw)
            if value is not None:
                state.add("times", value)
