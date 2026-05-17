#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

python3 "${REPO_ROOT}/scripts/migrate_subjects.py" \
  --pack literary_form \
  --pack audience \
  --pack genres \
  --pack subgenres \
  --pack content_formats \
  --pack moods \
  --pack literary_themes \
  --pack literary_tropes \
  --pack main_topics \
  --pack subject_diagnostics \
  --pack people \
  --pack places \
  --pack times \
  "$@"
