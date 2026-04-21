"""Shared helpers for subject-driven migration packs."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from core.run_state import RunState
from rule_engine.base import RulePack
from rules import RuleMatch


class SubjectMatchRule(Protocol):
    def match(self, raw: str) -> RuleMatch | None: ...


def first_match(raw: str, rules: Iterable[SubjectMatchRule]) -> RuleMatch | None:
    for rule in rules:
        match = rule.match(raw)
        if match is not None:
            return match
    return None


def apply_subject_migration(
    state: RunState,
    output_type: str,
    rules: Iterable[SubjectMatchRule],
) -> None:
    next_subjects: list[str] = []
    for raw in state.remaining_subjects:
        match = first_match(raw, rules)
        if match is None:
            next_subjects.append(raw)
            continue
        state.add(output_type, match.value)
        state.record_subject_match(
            raw=raw,
            output_type=output_type,
            value=match.value,
            action=match.action,
        )
        if match.action == "move":
            state.record_removed_subject(raw)
            continue
        state.record_retained_subject(raw)
        next_subjects.append(raw)
    state.remaining_subjects = next_subjects


class SubjectMigrationPack(RulePack):
    """Base class for packs that migrate legacy subjects into structured tags."""

    output_type: str = ""
    rules: Iterable[SubjectMatchRule]

    def apply(self, state: RunState) -> None:
        apply_subject_migration(
            state,
            output_type=self.output_type,
            rules=self.rules,
        )
