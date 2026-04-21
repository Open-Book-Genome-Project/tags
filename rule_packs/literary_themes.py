"""Rule pack for literary_themes tags."""

from __future__ import annotations

from collections.abc import Mapping

from rule_packs.utils import SubjectPack
from rules import MappingRule, PrefixRule


class LiteraryThemesPack(SubjectPack):
    name = "literary_themes"
    output_types = ("literary_themes",)
    output_type = "literary_themes"

    def __init__(
        self,
        mapping: Mapping[str, str] | None = None,
        remove_matched_subjects: bool = True,
    ) -> None:
        self.rules = (PrefixRule("theme"), MappingRule(mapping))
        self.remove_matched_subjects = remove_matched_subjects
