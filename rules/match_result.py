"""Structured subject-match results with per-rule actions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleMatch:
    """A normalized match value plus the subject-handling action to apply."""

    value: str
    action: str
