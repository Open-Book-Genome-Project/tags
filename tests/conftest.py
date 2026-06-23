"""
Shared fixtures for all test modules.
"""
import pytest


# ---------------------------------------------------------------------------
# Minimal work fixtures (golden set for classification tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def hp_work():
    """Harry Potter and the Sorcerer's Stone — OL82563W."""
    return {
        "key": "/works/OL82563W",
        "subjects": [
            "Fantasy fiction",
            "Wizards",
            "Magic",
            "juvenile fiction",
            "Boarding schools",
            "cyberpunk",
            "science fiction",
        ],
        "subject_people": ["Harry Potter", "Hermione Granger", "Albus Dumbledore"],
        "subject_places": ["Hogwarts", "England"],
        "subject_times": ["20th century"],
    }


@pytest.fixture
def wuthering_heights_work():
    """Wuthering Heights — OL45804W."""
    return {
        "key": "/works/OL45804W",
        "subjects": [
            "Romance fiction",
            "Gothic fiction",
            "Victorian literature",
            "Love stories",
        ],
        "subject_people": ["Heathcliff", "Catherine Earnshaw"],
        "subject_places": ["Yorkshire", "England"],
        "subject_times": ["19th century"],
    }


@pytest.fixture
def empty_work():
    return {"key": "/works/OL1W", "subjects": []}


# ---------------------------------------------------------------------------
# Minimal in-memory vocabulary dicts (for TagDB tests without disk I/O)
# ---------------------------------------------------------------------------

@pytest.fixture
def genres_vocab():
    return {
        "type": "genres",
        "label": "Genres",
        "controlled": True,
        "tags": [
            {
                "tag": "Fantasy",
                "slug": "fantasy",
                "definition": "Works set in imaginary worlds with magic or supernatural elements.",
                "aliases": ["high fantasy", "fantasy fiction"],
            },
            {
                "tag": "Horror",
                "slug": "horror",
                "definition": "Works whose primary intent is to produce fear.",
                "aliases": ["horror fiction"],
            },
            {
                "tag": "Sci-Fi",
                "slug": "sci-fi",
                "definition": "Works exploring speculative science or future settings.",
                "aliases": ["science fiction", "sf"],
            },
        ],
    }


@pytest.fixture
def subgenres_vocab():
    return {
        "type": "subgenres",
        "label": "Subgenres",
        "controlled": True,
        "tags": [
            {
                "tag": "Cyberpunk",
                "slug": "cyberpunk",
                "definition": "Near-future dystopia centered on technology and corporate power.",
                "parent_genres": ["sci-fi"],
                "aliases": [],
            },
        ],
    }


@pytest.fixture
def minimal_vocabularies(genres_vocab, subgenres_vocab):
    return [genres_vocab, subgenres_vocab]
