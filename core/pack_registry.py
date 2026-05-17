"""Stable pack-name registry for migration assembly."""

from __future__ import annotations

from typing import Callable

from core.json_loader import load_mapping, load_set
from rule_packs import (
    AudiencePack,
    ContentFormatsPack,
    GenresPack,
    LiteraryFormPack,
    LiteraryThemesPack,
    LiteraryTropesPack,
    MainTopicsPack,
    MoodsPack,
    PeoplePack,
    PlacesPack,
    SubgenresPack,
    SUBJECT_PACK_CLASSES,
    SubjectDiagnosticsPack,
    TimesPack,
)

PackFactory = Callable[[], object]

SUBJECT_PACK_BUILDERS = {pack_cls.name: pack_cls for pack_cls in SUBJECT_PACK_CLASSES}
PACK_PRESETS: dict[str, tuple[str, ...]] = {
    "subject_mappings": (
        "literary_form",
        "audience",
        "genres",
        "subgenres",
        "content_formats",
        "moods",
        "literary_themes",
        "literary_tropes",
        "main_topics",
        "subject_diagnostics",
        "people",
        "places",
        "times",
    ),
}

PACK_FACTORIES: dict[str, PackFactory] = {
    "literary_form": lambda: LiteraryFormPack(remove_matched_subjects=True),
    "audience": lambda: AudiencePack(
        mapping=load_mapping("audience"),
        remove_matched_subjects=True,
    ),
    "genres": lambda: GenresPack(
        mapping=load_mapping("genres"),
        remove_matched_subjects=True,
    ),
    "subgenres": lambda: SubgenresPack(
        mapping=load_mapping("subgenres"),
        remove_matched_subjects=True,
    ),
    "content_formats": lambda: ContentFormatsPack(
        mapping=load_mapping("content_formats"),
        remove_matched_subjects=True,
    ),
    "moods": lambda: MoodsPack(remove_matched_subjects=True),
    "literary_themes": lambda: LiteraryThemesPack(
        mapping=load_mapping("literary_themes"),
        remove_matched_subjects=True,
    ),
    "literary_tropes": lambda: LiteraryTropesPack(
        mapping=load_mapping("literary_tropes"),
        remove_matched_subjects=True,
    ),
    "main_topics": lambda: MainTopicsPack(
        mapping=load_mapping("main_topics"),
        remove_matched_subjects=True,
    ),
    "subject_diagnostics": lambda: SubjectDiagnosticsPack(
        droppable=load_set("droppable")
    ),
    "people": lambda: PeoplePack(overrides=load_mapping("people_overrides")),
    "places": lambda: PlacesPack(overrides=load_mapping("places_overrides")),
    "times": TimesPack,
}

AVAILABLE_PACK_NAMES = tuple(sorted({*PACK_FACTORIES, *PACK_PRESETS}))
