"""Rule pack for content_formats tags."""

from __future__ import annotations

from collections.abc import Mapping

from core.json_loader import load_mapping
from rule_packs.utils import SubjectPack
from rules import MappingRule, PrefixRule

MOVE = "move"
EXTRACT_ONLY = "extract_only"

# First-pass direct-match policies based on current dry-run evidence.
MOVE_TAGS = frozenset(
    {
        "Memoir",
        "Anthology",
        "Letters",
        "Dictionary",
    }
)


class ContentFormatsPack(SubjectPack):
    name = "content_formats"
    output_types = ("content_formats",)
    output_type = "content_formats"

    def __init__(
        self,
        move_mapping: Mapping[str, str] | None = None,
        extract_only_mapping: Mapping[str, str] | None = None,
    ) -> None:
        self.rules = (
            PrefixRule("format", action=EXTRACT_ONLY),
            MappingRule(move_mapping, default_action=MOVE),
            MappingRule(extract_only_mapping, default_action=EXTRACT_ONLY),
        )
        self.remove_matched_subjects = False

    @classmethod
    def default(cls) -> "ContentFormatsPack":
        mapping = load_mapping("content_formats")
        move_mapping = {
            legacy: canonical
            for legacy, canonical in mapping.items()
            if canonical in MOVE_TAGS
        }
        extract_only_mapping = {
            legacy: canonical
            for legacy, canonical in mapping.items()
            if canonical not in MOVE_TAGS
        }
        return cls(
            move_mapping=move_mapping,
            extract_only_mapping=extract_only_mapping,
        )
