"""Stable pack-name registry for migration assembly."""

from __future__ import annotations

from typing import Callable

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
    "literary_form": LiteraryFormPack.default,
    "audience": AudiencePack.default,
    "genres": GenresPack.default,
    "subgenres": SubgenresPack.default,
    "content_formats": ContentFormatsPack.default,
    "moods": MoodsPack.default,
    "literary_themes": LiteraryThemesPack.default,
    "literary_tropes": LiteraryTropesPack.default,
    "main_topics": MainTopicsPack.default,
    "subject_diagnostics": SubjectDiagnosticsPack.default,
    "people": PeoplePack.default,
    "places": PlacesPack.default,
    "times": TimesPack.default,
}

AVAILABLE_PACK_NAMES = tuple(sorted({*PACK_FACTORIES, *PACK_PRESETS}))
