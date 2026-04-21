# scripts

Tools for running the current subject-migration dry runs.

---

## Overview

The current migration scope is intentionally narrow:

- `content_formats` is the only actively developed type-specific migration pack
- `subject_diagnostics` is kept as a minimal QA/support pack

The goal of the script is to run subject-driven migration proposals against Open Library work JSON and show:

- which structured tags would be proposed
- which legacy subjects would be removed
- which legacy subjects would remain
- which subjects matched with `move` vs `extract_only`

---

## Scripts

### `migrate_subjects.py`

The current runner. Given a work's OL JSON, it:

1. Loads the legacy `subjects`, `subject_people`, `subject_places`, and `subject_times` lists
2. Applies the currently enabled subject packs
3. Outputs a proposal-style run report for review

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

# Run only content_formats
python scripts/migrate_subjects.py --file work.json --pack content_formats --dry-run

# Run content_formats plus diagnostics
python scripts/migrate_subjects.py --file work.json --pack subject_mappings --dry-run
```

Available packs:

- `content_formats`
- `subject_diagnostics`
- `subject_mappings` (preset for both)

**Output format:**
```json
{
  "work_id": "OL82563W",
  "proposed_tags": {
    "content_formats": ["Memoir", "Biography"],
    "reading_level": ["Grade 4"],
    "unmapped": ["abc"]
  },
  "subject_proposal": {
    "original": ["Memoirs", "Biography", "abc", "Grade 4"],
    "removed": ["Memoirs"],
    "remaining": ["Biography", "abc", "Grade 4"]
  },
  "subject_matches": [
    {
      "subject": "Memoirs",
      "output_type": "content_formats",
      "value": "Memoir",
      "action": "move"
    },
    {
      "subject": "Biography",
      "output_type": "content_formats",
      "value": "Biography",
      "action": "extract_only"
    }
  ]
}
```

This report is meant for dry-run review and QA, not as a final persisted work format.

---

### Architecture

The current implementation is intentionally small and only supports the present migration scope:

```text
core/
  json_loader.py         # JSON resource loading
  run_state.py           # shared run/proposal state
  subject_classifier.py  # work-level orchestration + report output
rule_engine/
  base.py                # RulePack interface
  normalization.py       # shared text normalization helpers
rules/
  match_result.py        # structured value + action matches
  mapping_rule.py        # normalized mapping matches
  prefix_rule.py         # prefix-based matches
rule_packs/
  content_formats.py     # current migration logic under active development
  subject_diagnostics.py # minimal QA/support pack
  utils.py               # shared subject-pack execution helper
```

`scripts/migrate_subjects.py` remains the operational entry point and keeps the pack selection local to the script.

### Adding Mapping Rules

Mappings live in `resources/mappings/`.

```
resources/
  mappings/
    content_formats.json  # legacy string → canonical format
    droppable.json        # strings to discard (reading levels, codes, etc.)
```

`content_formats.json` is a JSON object where keys are legacy subject strings and values are canonical content format tags:

```json
{
  "memoirs": "Memoir",
  "biography": "Biography",
  "letters": "Letters",
  "novels": "Novel"
}
```

`ContentFormatsPack` then splits those mappings into:

- `move` cases for currently clean first-pass formats
- `extract_only` cases for overlapping or not-yet-approved removals

## Development

```bash
pip install -r scripts/requirements.txt
python scripts/migrate_subjects.py --help
```

Requirements: `requests`, `tqdm` (for batch progress)

---

## Data Sources

- OL Work JSON: `https://openlibrary.org/works/{OL_ID}.json`
