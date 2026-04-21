# scripts

Tools for migrating Open Library's legacy subject strings to canonical typed tags.

---

## Overview

Open Library works currently have a flat `subjects` list (plus `subject_people`, `subject_places`, `subject_times`) containing a mix of genres, themes, tropes, catalog codes, reading levels, and noise. These scripts help convert that legacy data into structured, typed canonical tags.

---

## Scripts

### `migrate_subjects.py`

The current runner/compatibility entry point. Given a work's OL JSON, it:

1. Loads the legacy `subjects`, `subject_people`, `subject_places`, and `subject_times` lists
2. Builds a `SubjectClassifier` from one or more enabled rule packs
3. Applies rule-based and keyword matching to classify each string into the correct canonical type
3. Outputs a structured tag object ready for import into the new schema

**Usage:**
```bash
# Single work by OL ID
python scripts/migrate_subjects.py --work OL82563W

# From a local JSON file
python scripts/migrate_subjects.py --file work.json

# Legacy-compatible fixed-order wrapper
./scripts/run_legacy_subjects.sh --file work.json

# Batch from a newline-delimited list of OL IDs
python scripts/migrate_subjects.py --batch ol_ids.txt --output output/

# Dry run (print proposed mappings without writing)
python scripts/migrate_subjects.py --work OL82563W --dry-run

# Run the old full sequence explicitly through the wrapper
./scripts/run_legacy_subjects.sh --file work.json --dry-run

# Run only a subset of rule packs
python scripts/migrate_subjects.py --file work.json --pack genres --pack content_formats --pack subject_diagnostics --dry-run

# Run a single tag-type module
python scripts/migrate_subjects.py --file work.json --pack content_formats --dry-run
```

`migrate_subjects.py` no longer enables a default full preset when `--pack` is omitted. If you want the old full sequence, use `run_legacy_subjects.sh` or pass the pack list explicitly.

`run_legacy_subjects.sh` is just a thin wrapper around `migrate_subjects.py` with the pack order written out explicitly, so it is easy to inspect and change. Any extra CLI args are forwarded as-is.

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

### Architecture

The reusable classification core now lives outside the script entry point:

```text
core/
  json_loader.py                # JSON resource loading for default assembly
  subject_classifier.py         # public work-level orchestration core
  pack_registry.py              # stable pack names -> factories / presets
  classifier_assembler.py       # pack resolution + classifier assembly
  migrate_subject_classifier.py # compatibility shim for older imports
rule_engine/
  base.py                       # RulePack interface
  normalization.py              # shared text normalization helpers
rules/
  prefix_rule.py                # subject prefix matching
  mapping_rule.py               # normalized direct mapping
  override_rule.py              # override-based field normalization
  passthrough_rule.py           # cleaned passthrough fields
rule_packs/
  genres.py                     # one module per tag type
  content_formats.py
  audience.py
  literary_themes.py
  literary_tropes.py
  main_topics.py
  people.py
  places.py
  times.py
config/
  packs/                        # future static pack configs
```

`scripts/migrate_subjects.py` remains the operational entry point, but classification logic is now encapsulated in the shared core so future runners can reuse it.

The classification core itself is kept narrow: `SubjectClassifier` consumes a normalized `work` object plus already-constructed packs, and returns a result. JSON resource loading now lives in the default assembly layer rather than inside individual packs.

### Adding Mapping Rules

Mappings live in `resources/mappings/`. Each file covers one tag type:

```
resources/
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
