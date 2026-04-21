"""Rule pack for literary_form."""

from __future__ import annotations

from rule_packs.utils import SubjectPack
from rules import PrefixRule


class LiteraryFormPack(SubjectPack):
    name = "literary_form"
    output_types = ("literary_form",)
    output_type = "literary_form"

    def __init__(self, remove_matched_subjects: bool = True) -> None:
        self.rules = (PrefixRule("form"),)
        self.remove_matched_subjects = remove_matched_subjects

    @classmethod
    def default(cls) -> "LiteraryFormPack":
        return cls(remove_matched_subjects=True)
