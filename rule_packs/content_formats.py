"""Rule pack for content_formats tags."""

from __future__ import annotations

from collections.abc import Mapping

from core.json_loader import load_mapping
from rule_packs.utils import SubjectPack
from rules import MappingRule, PrefixRule


class ContentFormatsPack(SubjectPack):
    name = "content_formats"
    output_types = ("content_formats",)
    output_type = "content_formats"

    def __init__(
        self,
        mapping: Mapping[str, str] | None = None,
        remove_matched_subjects: bool = True,
    ) -> None:
        self.rules = (PrefixRule("format"), MappingRule(mapping))
        self.remove_matched_subjects = remove_matched_subjects

    @classmethod
    def default(cls) -> "ContentFormatsPack":
        return cls(
            mapping=load_mapping("content_formats"),
            remove_matched_subjects=True,
        )
