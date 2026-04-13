"""
Open Library Tags API

A lightweight FastAPI service for autocomplete search across the canonical
Open Library tag taxonomy. Powers patron-facing tag search and OL editing UI.

Run:
    uvicorn api.main:app --reload
    uvicorn api.main:app --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .db import TagDB
from .loader import load_all_vocabularies
from .models import Tag, TagSearchResponse, TypeInfo, TypeListResponse, TypeDetailResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = TagDB()
    vocabularies = load_all_vocabularies()
    db.seed(vocabularies)
    app.state.db = db
    yield
    db.close()


app = FastAPI(
    title="Open Library Tags API",
    description="Autocomplete and lookup API for the Open Library canonical tag taxonomy.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get(
    "/v1/tags",
    response_model=TagSearchResponse,
    summary="Search tags (autocomplete)",
    description=(
        "Search across all tag types, or within a specific type. "
        "Matches on tag name prefix first, then full-text across definitions. "
        "Designed for autocomplete UIs — returns fast, ranked results."
    ),
)
def search_tags(
    q: str = Query(default="", description="Search query (prefix or keyword)"),
    type: Optional[str] = Query(default=None, description="Filter to a specific tag type"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum results to return"),
):
    db: TagDB = app.state.db
    results = db.search(q=q, tag_type=type, limit=limit)
    return TagSearchResponse(query=q, type=type, count=len(results), results=results)


@app.get(
    "/v1/types",
    response_model=TypeListResponse,
    summary="List all tag types",
)
def list_types():
    db: TagDB = app.state.db
    types = db.list_types()
    return TypeListResponse(types=types)


@app.get(
    "/v1/types/{type_name}",
    response_model=TypeDetailResponse,
    summary="Get all tags for a type",
)
def get_type(type_name: str):
    db: TagDB = app.state.db
    result = db.get_type(type_name)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Tag type '{type_name}' not found")
    return result


@app.get(
    "/v1/types/{type_name}/{slug}",
    response_model=Tag,
    summary="Get a specific tag by type and slug",
)
def get_tag(type_name: str, slug: str):
    db: TagDB = app.state.db
    tag = db.get_tag(type_name=type_name, slug=slug)
    if tag is None:
        raise HTTPException(status_code=404, detail=f"Tag '{slug}' not found in type '{type_name}'")
    return tag


@app.get("/", include_in_schema=False)
def root():
    return {
        "service": "Open Library Tags API",
        "docs": "/docs",
        "version": "0.1.0",
    }
