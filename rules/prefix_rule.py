"""Prefix-based matching for subject values."""

from __future__ import annotations

from rules.match_result import RuleMatch


class PrefixRule:
    """Match values like ``theme:love`` and return the normalized payload."""

    def __init__(self, prefix: str, action: str = "move") -> None:
        self.prefix = prefix
        self.action = action

    def match(self, raw: str) -> RuleMatch | None:
        if not self.prefix or ":" not in raw:
            return None
        prefix, _, value = raw.partition(":")
        if prefix.strip().lower() != self.prefix:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        return RuleMatch(value=cleaned.title(), action=self.action)
