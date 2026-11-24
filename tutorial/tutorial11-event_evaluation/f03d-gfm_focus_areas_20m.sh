#!/usr/bin/env bash
set -euo pipefail

# Internal path anchors; user paths below are independent of the caller's directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
TUTORIAL_DIR="$SCRIPT_DIR"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"

# User settings
# ----------------------------------------------------------------------
PYTHON_CMD="${PYTHON_CMD:-python3}"                                   # Python executable; existing PYTHON_CMD override is supported.
EXTRACTED_AREAS="$TUTORIAL_DIR/metadata/03d_extracted_areas.json"     # Authoritative crop paths, bounds, classes and identities.
FIGURE_OUTPUT="$TUTORIAL_DIR/figure/f03d-gfm_focus_areas_20m.png"     # Output PNG path.
TILE_CACHE="$HOME/.cache/cmf_flood_osm_tiles"                         # OSM cache directory.
FIG_WIDTH=14                                                          # Canvas width [inches].
FIG_HEIGHT=0                                                          # Canvas height [inches]; 0 selects documented automatic height where supported.
DPI=150                                                               # PNG resolution [pixels/inch].
COLUMNS=3                                                             # Panel columns [1–6]; automatic height is 3.35 inches per row.

# ----------------------------------------------------------------------
# User settings end here.
# ----------------------------------------------------------------------

"$PYTHON_CMD" "$TUTORIAL_DIR/script/f03d-gfm_focus_areas_20m.py"  \
    --tutorial-dir "$TUTORIAL_DIR" \
    --extracted-areas "$EXTRACTED_AREAS" \
    --figure-output "$FIGURE_OUTPUT"  \
    --tile-cache "$TILE_CACHE" \
    --fig-width "$FIG_WIDTH" \
    --fig-height "$FIG_HEIGHT" \
    --dpi "$DPI" \
    --columns "$COLUMNS"
