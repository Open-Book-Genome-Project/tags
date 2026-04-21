"""Shared helpers for subject-based packs."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from core.run_state import RunState
from rule_engine.base import RulePack
from rules import RuleMatch


class SubjectValueRule(Protocol):
    def match(self, raw: str) -> RuleMatch | str | None: ...


def _coerce_match(match: RuleMatch | str, default_action: str) -> RuleMatch:
    if isinstance(match, RuleMatch):
        return match
    return RuleMatch(value=match, action=default_action)


def classify_subject_value(
    raw: str,
    rules: Iterable[SubjectValueRule],
    default_action: str,
) -> RuleMatch | None:
    for rule in rules:
        match = rule.match(raw)
        if match is not None:
            return _coerce_match(match, default_action)
    return None


def apply_subject_pack(
    state: RunState,
    output_type: str,
    rules: Iterable[SubjectValueRule],
    remove_matched_subjects: bool,
) -> None:
    default_action = "move" if remove_matched_subjects else "extract_only"
    next_subjects: list[str] = []
    for raw in state.remaining_subjects:
        match = classify_subject_value(raw, rules, default_action=default_action)
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


class SubjectPack(RulePack):
    """Small helper for packs that operate on the shared subject sequence."""

    output_type = ""

    def apply(self, state: RunState) -> None:
        apply_subject_pack(
            state,
            output_type=self.output_type,
            rules=self.rules,
            remove_matched_subjects=self.remove_matched_subjects,
        )
