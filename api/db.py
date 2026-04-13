"""
SQLite + FTS5 tag index.

The vocabulary.json files are the canonical source of truth.
This module builds an in-memory SQLite database from them on startup,
using FTS5 for fast prefix and full-text search.
"""

import json
import sqlite3
from typing import Optional

from .models import Tag, TypeInfo, TypeDetailResponse


CREATE_TAGS = """
CREATE TABLE IF NOT EXISTS tags (
    id            INTEGER PRIMARY KEY,
    tag           TEXT    NOT NULL,
    slug          TEXT    NOT NULL,
    type          TEXT    NOT NULL,
    definition    TEXT,
    parent_genres TEXT,   -- JSON array, NULL for non-subgenres
    aliases       TEXT,   -- JSON array of alternate names / legacy strings
    labels        TEXT,   -- JSON object of i18n display names {"fr": "Horreur", ...}
    descriptions  TEXT,   -- JSON object of i18n definitions
    UNIQUE(type, slug)
);
"""

CREATE_TYPES = """
CREATE TABLE IF NOT EXISTS types (
    type        TEXT PRIMARY KEY,
    label       TEXT NOT NULL,
    description TEXT,
    controlled  INTEGER NOT NULL DEFAULT 0
);
"""

# FTS5 content table pointing at `tags`
CREATE_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS tags_fts USING fts5(
    tag,
    definition,
    content=tags,
    content_rowid=id,
    tokenize='unicode61'
);
"""

# Keep FTS in sync via triggers
FTS_TRIGGERS = """
CREATE TRIGGER IF NOT EXISTS tags_ai AFTER INSERT ON tags BEGIN
    INSERT INTO tags_fts(rowid, tag, definition)
    VALUES (new.id, new.tag, new.definition);
END;

CREATE TRIGGER IF NOT EXISTS tags_ad AFTER DELETE ON tags BEGIN
    INSERT INTO tags_fts(tags_fts, rowid, tag, definition)
    VALUES ('delete', old.id, old.tag, old.definition);
END;

CREATE TRIGGER IF NOT EXISTS tags_au AFTER UPDATE ON tags BEGIN
    INSERT INTO tags_fts(tags_fts, rowid, tag, definition)
    VALUES ('delete', old.id, old.tag, old.definition);
    INSERT INTO tags_fts(rowid, tag, definition)
    VALUES (new.id, new.tag, new.definition);
END;
"""


class TagDB:
    def __init__(self, path: str = ":memory:"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._setup()

    def _setup(self):
        cur = self.conn.cursor()
        cur.executescript(CREATE_TAGS + CREATE_TYPES + CREATE_FTS + FTS_TRIGGERS)
        self.conn.commit()

    def seed(self, vocabularies: list[dict]):
        """Load all vocabulary dicts (from loader.py) into the DB."""
        cur = self.conn.cursor()
        for vocab in vocabularies:
            cur.execute(
                "INSERT OR REPLACE INTO types (type, label, description, controlled) VALUES (?,?,?,?)",
                (
                    vocab["type"],
                    vocab.get("label", vocab["type"]),
                    vocab.get("description"),
                    1 if vocab.get("controlled") else 0,
                ),
            )
            for t in vocab.get("tags", []):
                def _enc(v):
                    return json.dumps(v, ensure_ascii=False) if v else None

                cur.execute(
                    """
                    INSERT OR REPLACE INTO tags
                      (tag, slug, type, definition, parent_genres, aliases, labels, descriptions)
                    VALUES (?,?,?,?,?,?,?,?)
                    """,
                    (
                        t["tag"],
                        t["slug"],
                        vocab["type"],
                        t.get("definition"),
                        _enc(t.get("parent_genres")),
                        _enc(t.get("aliases")),
                        _enc(t.get("labels")),
                        _enc(t.get("descriptions")),
                    ),
                )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, q: str, tag_type: Optional[str] = None, limit: int = 10) -> list[Tag]:
        """
        Autocomplete search.

        Strategy (in priority order):
        1. Exact prefix match on tag name (case-insensitive)  → ranked first
        2. FTS5 full-text match on tag + definition           → ranked second

        Results are deduplicated and capped at `limit`.
        """
        q = q.strip()
        results: list[Tag] = []
        seen_ids: set[int] = set()

        type_filter = "AND t.type = ?" if tag_type else ""
        params_base = [tag_type] if tag_type else []

        # 1. Prefix match on tag name
        if q:
            prefix_sql = f"""
                SELECT t.id, t.tag, t.slug, t.type, t.definition, t.parent_genres, t.aliases, t.labels, t.descriptions
                FROM tags t
                WHERE t.tag LIKE ? {type_filter}
                ORDER BY length(t.tag), t.tag
                LIMIT ?
            """
            rows = self.conn.execute(
                prefix_sql, [f"{q}%"] + params_base + [limit]
            ).fetchall()
            for row in rows:
                if row["id"] not in seen_ids:
                    seen_ids.add(row["id"])
                    results.append(self._row_to_tag(row))

        # 2. FTS5 full-text search (fills remaining slots)
        if len(results) < limit and q:
            fts_query = " OR ".join(f'"{word}"*' for word in q.split()) if q else "*"
            fts_sql = f"""
                SELECT t.id, t.tag, t.slug, t.type, t.definition, t.parent_genres, t.aliases, t.labels, t.descriptions
                FROM tags_fts f
                JOIN tags t ON t.id = f.rowid
                WHERE tags_fts MATCH ? {type_filter}
                ORDER BY rank
                LIMIT ?
            """
            try:
                rows = self.conn.execute(
                    fts_sql, [fts_query] + params_base + [limit - len(results)]
                ).fetchall()
                for row in rows:
                    if row["id"] not in seen_ids:
                        seen_ids.add(row["id"])
                        results.append(self._row_to_tag(row))
            except sqlite3.OperationalError:
                # Malformed FTS query — skip gracefully
                pass

        # 3. If no query, return all of the (filtered) type up to limit
        if not q:
            list_sql = f"""
                SELECT t.id, t.tag, t.slug, t.type, t.definition, t.parent_genres, t.aliases, t.labels, t.descriptions
                FROM tags t
                WHERE 1=1 {type_filter}
                ORDER BY t.type, t.tag
                LIMIT ?
            """
            rows = self.conn.execute(list_sql, params_base + [limit]).fetchall()
            for row in rows:
                if row["id"] not in seen_ids:
                    seen_ids.add(row["id"])
                    results.append(self._row_to_tag(row))

        return results

    # ------------------------------------------------------------------
    # Types
    # ------------------------------------------------------------------

    def list_types(self) -> list[TypeInfo]:
        rows = self.conn.execute(
            "SELECT type, label, description, controlled FROM types ORDER BY type"
        ).fetchall()
        return [
            TypeInfo(
                type=r["type"],
                label=r["label"],
                description=r["description"],
                controlled=bool(r["controlled"]),
                tag_count=self._count_type(r["type"]),
            )
            for r in rows
        ]

    def get_type(self, type_name: str) -> Optional[TypeDetailResponse]:
        row = self.conn.execute(
            "SELECT type, label, description, controlled FROM types WHERE type = ?",
            [type_name],
        ).fetchone()
        if not row:
            return None
        tags = self.conn.execute(
            "SELECT id, tag, slug, type, definition, parent_genres, aliases, labels, descriptions FROM tags WHERE type = ? ORDER BY tag",
            [type_name],
        ).fetchall()
        return TypeDetailResponse(
            type=row["type"],
            label=row["label"],
            description=row["description"],
            controlled=bool(row["controlled"]),
            tag_count=len(tags),
            tags=[self._row_to_tag(t) for t in tags],
        )

    def get_tag(self, type_name: str, slug: str) -> Optional[Tag]:
        row = self.conn.execute(
            "SELECT id, tag, slug, type, definition, parent_genres, aliases, labels, descriptions FROM tags WHERE type = ? AND slug = ?",
            [type_name, slug],
        ).fetchone()
        return self._row_to_tag(row) if row else None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _count_type(self, type_name: str) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS n FROM tags WHERE type = ?", [type_name]
        ).fetchone()
        return row["n"]

    def _row_to_tag(self, row: sqlite3.Row) -> Tag:
        def _dec(v):
            if not v:
                return None
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None

        return Tag(
            tag=row["tag"],
            slug=row["slug"],
            type=row["type"],
            definition=row["definition"],
            parent_genres=_dec(row["parent_genres"]),
            aliases=_dec(row["aliases"]),
            labels=_dec(row["labels"]),
            descriptions=_dec(row["descriptions"]),
        )

    def close(self):
        self.conn.close()
