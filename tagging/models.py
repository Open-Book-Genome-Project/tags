"""Typed result models for subject classification."""

from __future__ import annotations

from typing import TypedDict


class ClassificationResult(TypedDict):
    literary_form: list[str]
    audience: list[str]
    genres: list[str]
    subgenres: list[str]
    content_formats: list[str]
    moods: list[str]
    literary_themes: list[str]
    literary_tropes: list[str]
    main_topics: list[str]
    sub_topics: list[str]
    people: list[str]
    places: list[str]
    times: list[str]
    things: list[str]
    reading_level: list[str]
    classification_codes: list[str]
    unmapped: list[str]
