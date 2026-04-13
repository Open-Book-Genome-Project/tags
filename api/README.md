# Tags API

A lightweight FastAPI microservice for autocomplete search across the Open Library canonical tag taxonomy.

---

## Architecture

```
vocabulary.json files (source of truth)
        │
        ▼
   loader.py  (discovers + reads all type dirs on startup)
        │
        ▼
    db.py     (SQLite + FTS5 in-memory index)
        │
        ▼
   main.py    (FastAPI app, routes)
```

**No external database required.** On startup, the service reads all `vocabulary.json` files from the repo, builds a SQLite in-memory index with FTS5 full-text search, and serves requests from there. Startup takes milliseconds. For small vocabularies (thousands of tags), in-memory is the right call.

The `vocabulary.json` files remain the canonical human-editable source. Restart the service to pick up changes.

---

## Running

```bash
# Install dependencies
pip install -r api/requirements.txt

# Run (from repo root)
uvicorn api.main:app --reload

# Production
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2
```

API docs available at: `http://localhost:8000/docs`

---

## Endpoints

### `GET /v1/tags`

Autocomplete search across all tags (or within a type).

| Parameter | Type | Default | Description |
|---|---|---|---|
| `q` | string | `""` | Search query — prefix or keyword |
| `type` | string | `null` | Filter to a specific type (e.g. `genres`, `moods`) |
| `limit` | int | `10` | Max results (1–100) |

**Search strategy (ranked):**
1. Prefix match on tag name (e.g. `hor` → `Horror`, `Harrowing`)
2. Full-text match on tag name + definition (FTS5)
3. If no query, returns all tags of the filtered type

**Examples:**
```
GET /v1/tags?q=goth
GET /v1/tags?q=goth&type=subgenres
GET /v1/tags?q=dark&type=moods&limit=5
GET /v1/tags?type=content_warnings
```

**Response:**
```json
{
  "query": "goth",
  "type": null,
  "count": 2,
  "results": [
    {
      "tag": "Gothic",
      "slug": "gothic",
      "type": "subgenres",
      "definition": "Atmospheric decay, ancestral secrets, the sublime...",
      "parent_genres": ["Horror", "Romance", "Literary"]
    },
    {
      "tag": "Gonzo",
      "slug": "gonzo",
      "type": "subgenres",
      "definition": "Subjective, chaotic, and author-centric...",
      "parent_genres": ["Literary", "Humor"]
    }
  ]
}
```

---

### `GET /v1/types`

List all registered tag types with metadata.

```json
{
  "types": [
    {
      "type": "genres",
      "label": "Genres",
      "description": "...",
      "controlled": true,
      "tag_count": 21
    },
    ...
  ]
}
```

---

### `GET /v1/types/{type_name}`

Get full details and all tags for a specific type.

```
GET /v1/types/moods
GET /v1/types/content_warnings
```

---

### `GET /v1/types/{type_name}/{slug}`

Get a specific tag.

```
GET /v1/types/subgenres/cyberpunk
GET /v1/types/moods/cozy
```

---

## Adding New Tags

The API is **read-only** in this version. To add tags:

1. Edit the relevant `vocabulary.json` in the type directory
2. Open a PR following [CONTRIBUTING.md](../CONTRIBUTING.md)
3. After merge, restart the service

**Future:** A write API (for patron proposals) is planned — see [ROADMAP.md](../ROADMAP.md).

---

## Source of Truth & GitHub Sync

The `vocabulary.json` files in each type directory are authoritative. To export a combined snapshot:

```bash
python scripts/dump_tags.py
```

This writes `tags.json` at the repo root — a single-file snapshot of all current tags, useful for:
- GitHub releases / changelogs
- Client-side use (embed the JSON directly, no API needed)
- Diffing changes in PRs
