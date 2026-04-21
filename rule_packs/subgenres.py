"""Rule pack for subgenre tags."""

from __future__ import annotations

from collections.abc import Mapping

from core.json_loader import load_mapping
from rule_packs.utils import SubjectPack
from rules import MappingRule, PrefixRule


class SubgenresPack(SubjectPack):
    name = "subgenres"
    output_types = ("subgenres",)
    output_type = "subgenres"

    def __init__(
        self,
        mapping: Mapping[str, str] | None = None,
        remove_matched_subjects: bool = True,
    ) -> None:
        self.rules = (PrefixRule("subgenre"), MappingRule(mapping))
        self.remove_matched_subjects = remove_matched_subjects

    @classmethod
    def default(cls) -> "SubgenresPack":
        return cls(
            mapping=load_mapping("subgenres"),
            remove_matched_subjects=True,
        )
