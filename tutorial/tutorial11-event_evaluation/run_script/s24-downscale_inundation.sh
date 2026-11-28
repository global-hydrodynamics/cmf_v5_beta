#!/usr/bin/env bash
set -euo pipefail

# Internal path anchors; user paths below are independent of the caller's directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
TUTORIAL_DIR="$(CDPATH= cd "$SCRIPT_DIR/.." && pwd -P)"
REPO_ROOT="$(cd "$TUTORIAL_DIR/../.." && pwd -P)"

# User settings
# ----------------------------------------------------------------------
PYTHON="$REPO_ROOT/.venv/bin/python"                                  # Python with NumPy and netCDF4; select an existing environment.
MAP_DIR="$TUTORIAL_DIR/map/Rhine_15min"                               # Tutorial-local 15min/1min map; existing method remains fixed.
DOWNSCALER="$REPO_ROOT/tools/downscale_flddph/script/downscale_flddph.py" # Maintained tributary-aware implementation; do not edit for routine settings.
MODEL_NETCDF="$TUTORIAL_DIR/experiment/Rhine2021/o_flddphRhine2021Jul.nc" # Model floodplain-depth input [m]; nearest existing CF time selected.
DOMAIN_CONFIG="$TUTORIAL_DIR/metadata/02_domain_selection.json"       # Authoritative 1min output bbox [west,south,east,north degrees].
SELECTION_JSON="$TUTORIAL_DIR/metadata/03a_selected_passes.json"      # Authoritative S1A orbit038784 selection/times; scope is one pass.
OUTPUT_DIR="$TUTORIAL_DIR/out"                                        # Derived depth directory; filename follows selected model time.
METADATA_OUTPUT="$TUTORIAL_DIR/metadata/24_downscaling_verification.json" # Canonical Step24 processing handoff JSON.

# ----------------------------------------------------------------------
# User settings end here.
# ----------------------------------------------------------------------

"$PYTHON" "$TUTORIAL_DIR/script/s24-downscale_inundation.py"  \
    --tutorial-dir "$TUTORIAL_DIR" \
    --map-dir "$MAP_DIR" \
    --downscaler "$DOWNSCALER"  \
    --model-netcdf "$MODEL_NETCDF" \
    --domain-config "$DOMAIN_CONFIG" \
    --selection-json "$SELECTION_JSON"  \
    --output-dir "$OUTPUT_DIR" \
    --metadata-output "$METADATA_OUTPUT"
