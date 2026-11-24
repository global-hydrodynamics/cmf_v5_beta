#!/usr/bin/env bash
set -eu

TUTORIAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "$TUTORIAL_DIR/../.." && pwd -P)"

# User settings: existing Rhine experiment/map; only S1A orbit 038784 is selected.
PYTHON="$REPO_ROOT/.venv/bin/python"                       # NumPy and netCDF4 environment.
MAP_DIR="$REPO_ROOT/map/Rhine_15min"                     # Matching 15min/1min river maps.
DOWNSCALER="$REPO_ROOT/tools/downscale_flddph/script/downscale_flddph.py"

# ========================================
# User settings end here.
# ========================================

"$PYTHON" "$TUTORIAL_DIR/script/s24-downscale_inundation.py" \
    --tutorial-dir "$TUTORIAL_DIR" --map-dir "$MAP_DIR" --downscaler "$DOWNSCALER"
