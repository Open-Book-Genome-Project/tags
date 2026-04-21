"""Passthrough normalization for field values."""

from __future__ import annotations


class PassthroughRule:
    """Return cleaned field values without additional transformation."""

    def apply(self, raw: str) -> str | None:
        cleaned = raw.strip()
        return cleaned or None
