"""Rule pack for audience tags."""

from __future__ import annotations

from collections.abc import Mapping

from core.json_loader import load_mapping
from rule_packs.utils import SubjectPack
from rules import MappingRule, PrefixRule


class AudiencePack(SubjectPack):
    name = "audience"
    output_types = ("audience",)
    output_type = "audience"

    def __init__(
        self,
        mapping: Mapping[str, str] | None = None,
        remove_matched_subjects: bool = True,
    ) -> None:
        self.rules = (PrefixRule("audience"), MappingRule(mapping))
        self.remove_matched_subjects = remove_matched_subjects

    @classmethod
    def default(cls) -> "AudiencePack":
        return cls(
            mapping=load_mapping("audience"),
            remove_matched_subjects=True,
        )
