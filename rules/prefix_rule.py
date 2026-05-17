"""Prefix-based matching for subject values."""

from __future__ import annotations


class PrefixRule:
    """Match values like ``theme:love`` and return the normalized payload."""

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    def match(self, raw: str) -> str | None:
        if not self.prefix or ":" not in raw:
            return None
        prefix, _, value = raw.partition(":")
        if prefix.strip().lower() != self.prefix:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        return cleaned.title()
