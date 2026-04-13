from typing import Optional
from pydantic import BaseModel


class Tag(BaseModel):
    tag: str
    slug: str
    type: str
    definition: Optional[str] = None
    parent_genres: Optional[list[str]] = None
    # Forward-compat fields — populated as the vocabulary matures
    aliases: Optional[list[str]] = None       # alternate names / legacy strings that map here
    labels: Optional[dict[str, str]] = None   # i18n display names, e.g. {"fr": "Horreur"}
    descriptions: Optional[dict[str, str]] = None  # i18n definitions


class TagSearchResponse(BaseModel):
    query: str
    type: Optional[str] = None
    count: int
    results: list[Tag]


class TypeInfo(BaseModel):
    type: str
    label: str
    description: Optional[str] = None
    controlled: bool
    tag_count: int


class TypeListResponse(BaseModel):
    types: list[TypeInfo]


class TypeDetailResponse(BaseModel):
    type: str
    label: str
    description: Optional[str] = None
    controlled: bool
    tag_count: int
    tags: list[Tag]
