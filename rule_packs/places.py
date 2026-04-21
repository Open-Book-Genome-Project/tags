"""Rule pack for subject_places."""

from __future__ import annotations

from collections.abc import Mapping

from core.run_state import RunState
from rule_engine.base import RulePack
from rules import OverrideRule


class PlacesPack(RulePack):
    name = "places"
    output_types = ("places",)

    def __init__(self, overrides: Mapping[str, str] | None = None) -> None:
        self.rule = OverrideRule(overrides)

    def apply(self, state: RunState) -> None:
        for raw in state.work.get("subject_places", []):
            value = self.rule.apply(raw)
            if value is not None:
                state.add("places", value)
