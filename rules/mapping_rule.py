"""Direct mapping lookups for normalized values."""

from __future__ import annotations

from collections.abc import Mapping

from rule_engine.normalization import normalize
from rules.match_result import RuleMatch


class MappingRule:
    """Match normalized input values against a provided mapping."""

    def __init__(
        self,
        mapping: Mapping[str, str] | None = None,
        default_action: str = "move",
    ) -> None:
        self.mapping = dict(mapping or {})
        self.default_action = default_action

    def match(self, raw: str) -> RuleMatch | None:
        value = self.mapping.get(normalize(raw))
        if value is None:
            return None
        return RuleMatch(value=value, action=self.default_action)
