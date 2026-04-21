"""LCSH '--' suffix extraction for normalized values."""

from __future__ import annotations

from collections.abc import Mapping

from rule_engine.normalization import normalize


class LCSHSuffixRule:
    """Extract genre signals from LCSH '--' suffix patterns.

    Handles subject strings like 'Pirates--Fiction' or 'History--Biography'
    by splitting on '--' and matching the suffix against a provided mapping.

    Example:
        'Pirates--Fiction' -> 'Fiction'
        'History--Biography' -> 'Nonfiction'
    """

    def __init__(self, mapping: Mapping[str, str] | None = None) -> None:
        self.mapping = dict(mapping or {})

    def match(self, raw: str) -> str | None:
        key = normalize(raw)
        if "--" not in key:
            return None
        suffix = key.split("--")[-1].strip()
        return self.mapping.get(suffix)
