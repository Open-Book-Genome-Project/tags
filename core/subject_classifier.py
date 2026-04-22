"""Reusable classification core for subject migration."""

from __future__ import annotations

from core.json_loader import load_mapping, load_set
from rule_engine.normalization import (
    is_classification_code,
    is_reading_level,
    normalize,
)


class SubjectClassifier:
    """Classify legacy Open Library subjects into typed tags."""

    def __init__(self) -> None:
        self.genres_map = load_mapping("genres")
        self.subgenres_map = load_mapping("subgenres")
        self.formats_map = load_mapping("content_formats")
        self.themes_map = load_mapping("literary_themes")
        self.tropes_map = load_mapping("literary_tropes")
        self.topics_map = load_mapping("main_topics")
        self.audience_map = load_mapping("audience")
        self.droppable = load_set("droppable")
        self.people_overrides = load_mapping("people_overrides")
        self.places_overrides = load_mapping("places_overrides")

    def classify_subject(self, raw: str) -> tuple[str, str | None]:
        """
        Classify a single subject string.

        Returns (type, canonical_value) where type is one of:
          literary_form, genres, subgenres, content_formats, literary_themes,
          literary_tropes, main_topics, audience, reading_level,
          classification_code, drop, unmapped
        """
        key = normalize(raw)

        if key in self.audience_map:
            return ("audience", self.audience_map[key])

        if key in self.droppable:
            return ("drop", None)

        if is_reading_level(raw):
            return ("reading_level", raw.strip())

        if is_classification_code(raw):
            return ("classification_code", raw.strip())

        if ":" in raw:
            prefix, _, value = raw.partition(":")
            prefix = prefix.strip().lower()
            value = value.strip()
            type_map = {
                "form": "literary_form",
                "audience": "audience",
                "genre": "genres",
                "subgenre": "subgenres",
                "format": "content_formats",
                "theme": "literary_themes",
                "trope": "literary_tropes",
                "topic": "main_topics",
                "mood": "moods",
            }
            if prefix in type_map:
                return (type_map[prefix], value.title())

        if key in self.genres_map:
            return ("genres", self.genres_map[key])
        if key in self.subgenres_map:
            return ("subgenres", self.subgenres_map[key])
        if key in self.formats_map:
            return ("content_formats", self.formats_map[key])
        if key in self.themes_map:
            return ("literary_themes", self.themes_map[key])
        if key in self.tropes_map:
            return ("literary_tropes", self.tropes_map[key])
        if key in self.topics_map:
            return ("main_topics", self.topics_map[key])

        return ("unmapped", raw.strip())

    def classify_work(self, work: dict) -> dict:
        """Given a work JSON dict, produce a structured tag output."""
        result: dict[str, list] = {
            "literary_form": [],
            "audience": [],
            "genres": [],
            "subgenres": [],
            "content_formats": [],
            "moods": [],
            "literary_themes": [],
            "literary_tropes": [],
            "main_topics": [],
            "sub_topics": [],
            "people": [],
            "places": [],
            "times": [],
            "things": [],
            "reading_level": [],
            "classification_codes": [],
            "unmapped": [],
        }

        for raw in work.get("subjects", []):
            tag_type, value = self.classify_subject(raw)
            if tag_type == "drop" or value is None:
                continue
            if tag_type == "reading_level":
                result["reading_level"].append(value)
            elif tag_type == "classification_code":
                result["classification_codes"].append(value)
            elif tag_type in result:
                if value not in result[tag_type]:
                    result[tag_type].append(value)
            else:
                result["unmapped"].append(raw)

        for raw in work.get("subject_people", []):
            key = normalize(raw)
            canonical = self.people_overrides.get(key, raw.strip())
            if canonical not in result["people"]:
                result["people"].append(canonical)

        for raw in work.get("subject_places", []):
            key = normalize(raw)
            canonical = self.places_overrides.get(key, raw.strip())
            if canonical not in result["places"]:
                result["places"].append(canonical)

        for raw in work.get("subject_times", []):
            cleaned = raw.strip()
            if cleaned and cleaned not in result["times"]:
                result["times"].append(cleaned)

        return result
