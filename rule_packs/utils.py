"""Shared helpers for subject-based packs."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from core.run_state import RunState
from rule_engine.base import RulePack


class SubjectValueRule(Protocol):
    def match(self, raw: str) -> str | None: ...


def classify_subject_value(raw: str, rules: Iterable[SubjectValueRule]) -> str | None:
    for rule in rules:
        match = rule.match(raw)
        if match is not None:
            return match
    return None


def classify_subject_values(
    state: RunState,
    output_type: str,
    rules: Iterable[SubjectValueRule],
) -> None:
    next_subjects: list[str] = []
    for raw in state.remaining_subjects:
        match = classify_subject_value(raw, rules)
        if match is None:
            next_subjects.append(raw)
            continue
        state.add(output_type, match)
        state.record_subject_match(
            raw=raw,
            output_type=output_type,
            value=match,
            action="move",
        )
        state.record_removed_subject(raw)
    state.remaining_subjects = next_subjects


def apply_subject_pack(
    state: RunState,
    output_type: str,
    rules: Iterable[SubjectValueRule],
    remove_matched_subjects: bool,
) -> None:
    if remove_matched_subjects:
        classify_subject_values(state, output_type, rules)
        return
    for raw in state.remaining_subjects:
        match = classify_subject_value(raw, rules)
        if match is not None:
            state.add(output_type, match)
            state.record_subject_match(
                raw=raw,
                output_type=output_type,
                value=match,
                action="extract_only",
            )


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
