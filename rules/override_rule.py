"""Override-based normalization for field values."""

from __future__ import annotations

from collections.abc import Mapping

from rule_engine.normalization import normalize


class OverrideRule:
    """Normalize a field value using overrides with raw fallback."""

    def __init__(self, overrides: Mapping[str, str] | None = None) -> None:
        self.overrides = dict(overrides or {})

    def apply(self, raw: str) -> str | None:
        cleaned = raw.strip()
        if not cleaned:
            return None
        return self.overrides.get(normalize(raw), cleaned)
