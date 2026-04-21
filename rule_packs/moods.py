"""Rule pack for moods tags."""

from __future__ import annotations

from rule_packs.utils import SubjectPack
from rules import PrefixRule


class MoodsPack(SubjectPack):
    name = "moods"
    output_types = ("moods",)
    output_type = "moods"

    def __init__(self, remove_matched_subjects: bool = True) -> None:
        self.rules = (PrefixRule("mood"),)
        self.remove_matched_subjects = remove_matched_subjects

    @classmethod
    def default(cls) -> "MoodsPack":
        return cls(remove_matched_subjects=True)
