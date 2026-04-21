"""Rule pack for main_topics tags."""

from __future__ import annotations

from collections.abc import Mapping

from core.json_loader import load_mapping
from rule_packs.utils import SubjectPack
from rules import MappingRule, PrefixRule


class MainTopicsPack(SubjectPack):
    name = "main_topics"
    output_types = ("main_topics",)
    output_type = "main_topics"

    def __init__(
        self,
        mapping: Mapping[str, str] | None = None,
        remove_matched_subjects: bool = True,
    ) -> None:
        self.rules = (PrefixRule("topic"), MappingRule(mapping))
        self.remove_matched_subjects = remove_matched_subjects

    @classmethod
    def default(cls) -> "MainTopicsPack":
        return cls(
            mapping=load_mapping("main_topics"),
            remove_matched_subjects=True,
        )
