"""Concrete rule-pack modules."""

from .audience import AudiencePack
from .content_formats import ContentFormatsPack
from .genres import GenresPack
from .literary_form import LiteraryFormPack
from .literary_themes import LiteraryThemesPack
from .literary_tropes import LiteraryTropesPack
from .main_topics import MainTopicsPack
from .moods import MoodsPack
from .people import PeoplePack
from .places import PlacesPack
from .subgenres import SubgenresPack
from .subject_diagnostics import SubjectDiagnosticsPack
from .times import TimesPack

SUBJECT_PACK_CLASSES = (
    LiteraryFormPack,
    AudiencePack,
    GenresPack,
    SubgenresPack,
    ContentFormatsPack,
    MoodsPack,
    LiteraryThemesPack,
    LiteraryTropesPack,
    MainTopicsPack,
)

FIELD_PACK_CLASSES = (
    PeoplePack,
    PlacesPack,
    TimesPack,
)

ALL_PACK_CLASSES = SUBJECT_PACK_CLASSES + FIELD_PACK_CLASSES

__all__ = [
    "ALL_PACK_CLASSES",
    "AudiencePack",
    "ContentFormatsPack",
    "FIELD_PACK_CLASSES",
    "GenresPack",
    "LiteraryFormPack",
    "LiteraryThemesPack",
    "LiteraryTropesPack",
    "MainTopicsPack",
    "MoodsPack",
    "PeoplePack",
    "PlacesPack",
    "SUBJECT_PACK_CLASSES",
    "SubgenresPack",
    "SubjectDiagnosticsPack",
    "TimesPack",
]
