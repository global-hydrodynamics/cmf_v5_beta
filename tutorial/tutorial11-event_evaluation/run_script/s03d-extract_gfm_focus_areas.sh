#!/usr/bin/env bash
set -euo pipefail

# Internal path anchors; user paths below are independent of the caller's directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
TUTORIAL_DIR="$(CDPATH= cd "$SCRIPT_DIR/.." && pwd -P)"
REPO_ROOT="$(cd "$TUTORIAL_DIR/../.." && pwd -P)"

# User settings
# ----------------------------------------------------------------------
PYTHON_CMD="${PYTHON_CMD:-python3}"                                   # Python executable; existing PYTHON_CMD override is supported.
FOCUS_AREAS="$TUTORIAL_DIR/metadata/03c_focus_areas.json"             # Authoritative selected WGS84 boxes and pass ID.
SOURCE_TIFF="$TUTORIAL_DIR/observation/GFM_extent/GFM_S1A_20210715_o038784_dt049389_extent20m.tif" # Existing native 20m class raster; no resampling.
SOURCE_METADATA="$TUTORIAL_DIR/observation/GFM_extent/GFM_S1A_20210715_o038784_dt049389_extent20m.json" # Source classification provenance JSON.
OUTPUT_DIR="$TUTORIAL_DIR/observation/GFM_extent"                     # Native focus-crop destination directory.
OUTPUT_METADATA="$TUTORIAL_DIR/metadata/03d_extracted_areas.json"     # Canonical crop handoff JSON.

# ----------------------------------------------------------------------
# User settings end here.
# ----------------------------------------------------------------------

"$PYTHON_CMD" "$TUTORIAL_DIR/script/s03d-extract_gfm_focus_areas.py"  \
    --tutorial-dir "$TUTORIAL_DIR" \
    --focus-areas "$FOCUS_AREAS" \
    --source-tiff "$SOURCE_TIFF"  \
    --source-metadata "$SOURCE_METADATA" \
    --output-dir "$OUTPUT_DIR" \
    --output-metadata "$OUTPUT_METADATA"
