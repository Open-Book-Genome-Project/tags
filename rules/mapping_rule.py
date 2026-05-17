"""Direct mapping lookups for normalized values."""

from __future__ import annotations

from collections.abc import Mapping

from rule_engine.normalization import normalize


class MappingRule:
    """Match normalized input values against a provided mapping."""

    def __init__(self, mapping: Mapping[str, str] | None = None) -> None:
        self.mapping = dict(mapping or {})

    def match(self, raw: str) -> str | None:
        return self.mapping.get(normalize(raw))
