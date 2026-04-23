# scripts

Tools for migrating Open Library's legacy subject strings to canonical typed tags.

---

## Overview

Open Library works currently have a flat `subjects` list (plus `subject_people`, `subject_places`, `subject_times`) containing a mix of genres, themes, tropes, catalog codes, reading levels, and noise. These scripts help convert that legacy data into structured, typed canonical tags.

---

## Scripts

### `migrate_subjects.py`

The main migration tool. Given a work's OL JSON, it:

1. Loads the legacy `subjects`, `subject_people`, `subject_places`, and `subject_times` lists
2. Applies rule-based and keyword matching to classify each string into the correct canonical type
3. Outputs a structured tag object ready for import into the new schema

The CLI remains the entry point, but the reusable tagging logic now lives in a package-style layout:

- `tagging/__init__.py` for the public re-export surface
- `tagging/engine.py` for the `TypedTagger` implementation
- `tagging/normalization.py` for pure normalization and classification helpers
- `tagging/json_loader.py` for mapping JSON I/O
- `tagging/models.py` for typed result structures

**Usage:**
```bash
# Single work by OL ID
python scripts/migrate_subjects.py --work OL82563W

# From a local JSON file
python scripts/migrate_subjects.py --file work.json

# Batch from a newline-delimited list of OL IDs
python scripts/migrate_subjects.py --batch ol_ids.txt --output output/

# Dry run (print proposed mappings without writing)
python scripts/migrate_subjects.py --work OL82563W --dry-run
```

**Output format:**
```json
{
  "work_id": "OL82563W",
  "literary_form": ["Fiction"],
  "genres": ["Tragedy", "Gothic", "Romance"],
  "subgenres": ["Psychological", "Historical"],
  "content_formats": ["Novel"],
  "moods": [],
  "literary_themes": ["Love", "Revenge", "Death"],
  "literary_tropes": ["Foundlings", "Love Triangles"],
  "main_topics": ["Interpersonal relations", "Family life", "Class"],
  "sub_topics": ["Country life", "Rural families", "Landscape"],
  "people": ["Heathcliff", "Catherine Earnshaw"],
  "places": ["Yorkshire", "England"],
  "times": [],
  "things": [],
  "unmapped": ["Pr4172 .w7 2009c", "823/.8", "Zhang pian xiao shuo"]
}
```

The `unmapped` field collects strings that couldn't be classified — these are candidates for manual review or the `other` / droppable bucket.

---

### Adding Mapping Rules

Mappings live in `scripts/mappings/`. Each file covers one tag type:

```
scripts/
  mappings/
    genres.json          # legacy string → canonical genre
    subgenres.json        # legacy string → canonical subgenre
    content_formats.json  # legacy string → canonical format
    literary_themes.json  # legacy string → canonical theme
    literary_tropes.json  # legacy string → canonical trope
    droppable.json        # strings to discard (reading levels, codes, etc.)
    people_overrides.json # OL people string → canonical name
    places_overrides.json # OL place string → canonical place
```

Each mapping file is a JSON object where keys are legacy strings (lowercase, stripped) and values are the canonical tag:

```json
{
  "historical fiction": "Historical",
  "fiction, historical": "Historical",
  "psychological fiction": "Psychological",
  "gothic fiction": "Gothic",
  "english gothic fiction": "Gothic"
}
```

To add a new mapping: edit the appropriate file and open a PR. No code changes needed for new string mappings.

---

## Development

```bash
pip install -r scripts/requirements.txt
python scripts/migrate_subjects.py --help
```

Requirements: `requests`, `tqdm` (for batch progress)

---

## Data Sources

- OL Work JSON: `https://openlibrary.org/works/{OL_ID}.json`
- OL Search API: `https://openlibrary.org/search.json`
- Tag objects: `https://openlibrary.org/tags/{TAG_ID}.json`
