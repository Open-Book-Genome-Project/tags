"""Rule pack for literary_form."""

from __future__ import annotations

import json
from pathlib import Path

from rule_engine.normalization import normalize
from rule_packs.utils import SubjectPack
from rules import LCSHSuffixRule, MappingRule, PrefixRule

MAPPINGS_DIR = Path(__file__).parent.parent / "resources" / "mappings"

# Strong Nonfiction signals used for conflict resolution.
# These are subjects that unambiguously indicate Nonfiction even when
# Fiction signals are also present. Topic subdivisions like "history"
# are intentionally excluded - they appear on both Fiction and Nonfiction works.
STRONG_NONFICTION_SIGNALS = {
    "biography",
    "biographies",
    "autobiography",
    "autobiographies",
    "biographical",
    "autobiographical",
    "memoir",
    "memoirs",
    "juvenile nonfiction",
}

class DroppableRule:
    """Drop known noise strings - import artifacts, access markers, etc.

    Returns a sentinel value "__drop__" for matched strings so the pack
    can skip them without classifying them as any literary form.
    """

    def __init__(self, droppable: set[str]) -> None:
        self.droppable = droppable

    def match(self, raw: str) -> str | None:
        if normalize(raw) in self.droppable:
            return "__drop__"
        return None


class LiteraryFormPack(SubjectPack):
    """Rule pack for literary_form classification.

    Applies rules in strict precision order:
      1. DroppableRule  - noise strings are silently skipped
      2. PrefixRule     - explicit typed tags like 'form:novel'
      3. MappingRule    - direct case-insensitive mapping lookup
      4. LCSHSuffixRule - LCSH '--' suffix extraction

    Conflict resolution:
      If both Fiction and Nonfiction are matched from a work's subjects,
      Fiction wins by default UNLESS a strong unambiguous Nonfiction marker
      is present (biography, memoir, autobiography, etc.).
      This prevents topic subdivisions like 'history' from overriding
      a Fiction classification on historical fiction works.
    """

    name = "literary_form"
    output_types = ("literary_form",)
    output_type = "literary_form"

    def __init__(self, remove_matched_subjects: bool = True) -> None:
        literary_form_map = self._load_mapping("literary_form.json")
        droppable = self._load_droppable("droppable.json")

        self.rules = (
            DroppableRule(droppable),
            PrefixRule("form"),
            MappingRule(literary_form_map),
            LCSHSuffixRule(literary_form_map),
        )
        self.remove_matched_subjects = remove_matched_subjects
        self._literary_form_map = literary_form_map

    def _load_mapping(self, filename: str) -> dict[str, str]:
        path = MAPPINGS_DIR / filename
        if not path.exists():
            return {}
        with open(path) as f:
            return json.load(f)

    def _load_droppable(self, filename: str) -> set[str]:
        path = MAPPINGS_DIR / filename
        if not path.exists():
            return set()
        with open(path) as f:
            data = json.load(f)
        return {s.lower().strip() for s in data}

    def apply(self, state) -> None:
        """Classify subjects and resolve Fiction/Nonfiction conflicts."""
        matched_values = []
        next_subjects = []

        for raw in state.remaining_subjects:
            value = None
            for rule in self.rules:
                result = rule.match(raw)
                if result is not None:
                    value = result
                    break

            if value == "__drop__":
                # Noise string - consume it silently
                continue
            elif value is not None:
                matched_values.append(value)
                if not self.remove_matched_subjects:
                    next_subjects.append(raw)
            else:
                next_subjects.append(raw)

        if self.remove_matched_subjects:
            state.remaining_subjects = next_subjects

        # Conflict resolution: Fiction vs Nonfiction
        has_fiction = "Fiction" in matched_values
        has_nonfiction = "Nonfiction" in matched_values

        if has_fiction and has_nonfiction:
            # Check if any strong Nonfiction signal is present in original subjects
            subjects_lower = {normalize(s) for s in state.work.get("subjects", [])}
            if subjects_lower & STRONG_NONFICTION_SIGNALS:
                resolved = ["Nonfiction"]
            else:
                resolved = ["Fiction"]
        elif has_fiction:
            resolved = ["Fiction"]
        elif has_nonfiction:
            resolved = ["Nonfiction"]
        else:
            resolved = list(dict.fromkeys(matched_values))  # deduplicate, preserve order

        for value in resolved:
            state.add(self.output_type, value)
