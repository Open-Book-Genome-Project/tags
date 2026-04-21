"""Rule pack for genre tags."""

from __future__ import annotations

from collections.abc import Mapping

from rule_packs.utils import SubjectPack
from rules import MappingRule, PrefixRule


class GenresPack(SubjectPack):
    name = "genres"
    output_types = ("genres",)
    output_type = "genres"

    def __init__(
        self,
        mapping: Mapping[str, str] | None = None,
        remove_matched_subjects: bool = True,
    ) -> None:
        self.rules = (PrefixRule("genre"), MappingRule(mapping))
        self.remove_matched_subjects = remove_matched_subjects
