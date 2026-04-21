"""Concrete rule-pack modules."""

from .content_formats import ContentFormatsPack
from .subject_diagnostics import SubjectDiagnosticsPack

SUBJECT_PACK_CLASSES = (ContentFormatsPack,)

FIELD_PACK_CLASSES = ()

ALL_PACK_CLASSES = SUBJECT_PACK_CLASSES + FIELD_PACK_CLASSES

__all__ = [
    "ALL_PACK_CLASSES",
    "ContentFormatsPack",
    "FIELD_PACK_CLASSES",
    "SUBJECT_PACK_CLASSES",
    "SubjectDiagnosticsPack",
]
