#!/usr/bin/env bash
set -euo pipefail

# User settings
PYTHON_CMD="${PYTHON_CMD:-python3}"

TUTORIAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$PYTHON_CMD" "$TUTORIAL_DIR/script/s03d-extract_gfm_focus_areas.py" \
    --tutorial-dir "$TUTORIAL_DIR" \
    --focus-areas "$TUTORIAL_DIR/metadata/f03c_focus_areas.json" \
    --source-tiff "$TUTORIAL_DIR/observation/GFM_extent/GFM_S1A_20210715_o038784_dt049389_extent20m.tif" \
    --source-metadata "$TUTORIAL_DIR/observation/GFM_extent/GFM_S1A_20210715_o038784_dt049389_extent20m.json" \
    --output-dir "$TUTORIAL_DIR/observation/GFM_extent" \
    --output-metadata "$TUTORIAL_DIR/metadata/03d_extracted_areas.json"
