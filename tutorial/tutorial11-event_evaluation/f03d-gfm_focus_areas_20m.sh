#!/usr/bin/env bash
set -euo pipefail

# User settings
PYTHON_CMD="${PYTHON_CMD:-python3}"

TUTORIAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$PYTHON_CMD" "$TUTORIAL_DIR/script/f03d-gfm_focus_areas_20m.py" \
    --tutorial-dir "$TUTORIAL_DIR" \
    --extracted-areas "$TUTORIAL_DIR/metadata/03d_extracted_areas.json" \
    --figure-output "$TUTORIAL_DIR/figure/f03d-gfm_focus_areas_20m.png" \
    --tile-cache "$HOME/.cache/cmf_flood_osm_tiles"
