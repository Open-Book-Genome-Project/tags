"""Rule-pack interface for the migration core."""

from __future__ import annotations

from core.run_state import RunState


class RulePack:
    """A bounded unit of classification logic for one or more output types."""

    name = ""
    output_types: tuple[str, ...] = ()

    def apply(self, state: RunState) -> None:
        raise NotImplementedError
