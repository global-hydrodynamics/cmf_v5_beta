#!/usr/bin/env bash
# Generate Tutorial 11 Figures 15a and 15b from the retained Step 14 outputs.
set -euo pipefail
export MPLBACKEND=Agg

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TUTORIAL_DIR="$(CDPATH= cd "$SCRIPT_DIR/.." && pwd -P)"
REPO_ROOT="$(cd "$TUTORIAL_DIR/../.." && pwd)"

# User settings
# ----------------------------------------------------------------------
PYTHON="${PYTHON:-$REPO_ROOT/.venv/bin/python}" # Python with NumPy, netCDF4 and Matplotlib; existing env override supported.
STEP14_METADATA="$TUTORIAL_DIR/metadata/14_simulation_setup.json" # Authoritative experiment paths, period and variable semantics.
DOMAIN_METADATA="$TUTORIAL_DIR/metadata/02_domain_selection.json" # Authoritative AOI bounds [west,south,east,north degrees].
MAP_DIR="$TUTORIAL_DIR/map/Rhine_15min" # Tutorial-local matching coarse/high-resolution map root.
ANALYSIS_FILE="$TUTORIAL_DIR/experiment/Rhine2021/analysis/maximum_discharge_20210701-20210801.nc" # Derived signed local-peak NetCDF output; not a simultaneous state.
FIGURE_DIR="$TUTORIAL_DIR/figure" # Output PNG directory.
REGIONAL_FIGURE="$FIGURE_DIR/f15a-maximum_discharge-regional.png" # Regional signed-peak PNG.
AOI_FIGURE="$FIGURE_DIR/f15b-maximum_discharge-aoi.png" # AOI signed-peak PNG.
COLOR_LEVELS="-1500,-1000,-300,-100,-30,-10,0,10,30,100,300,1000,3000,8000,15000" # Signed discharge color boundaries [m3/s], comma-separated increasing values.
LINTHRESH="10" # Symmetric-log linear transition scale [m3/s], positive.
LINEAR_FRAC="0.10" # Display fraction occupied by linear range [0–1].
DPI=200 # PNG resolution [pixels/inch].

REGIONAL_HEIGHT=10.0 # Regional canvas height [inches]; width preserves existing aspect.
AOI_HEIGHT=9.0 # AOI canvas height [inches]; width preserves existing aspect.

# ----------------------------------------------------------------------
# User settings end here.
# ----------------------------------------------------------------------

printf '\n[STEP 1/2] Compute signed local peaks from Step 14 hourly outputs.\n'
"$PYTHON" "$TUTORIAL_DIR/script/f15-maximum_discharge.py" \
    --step14-metadata "$STEP14_METADATA" \
    --domain-metadata "$DOMAIN_METADATA" \
    --map-dir "$MAP_DIR" \
    --tutorial-dir "$TUTORIAL_DIR" \
    --analysis-file "$ANALYSIS_FILE" \
    --regional-figure "$REGIONAL_FIGURE" \
    --aoi-figure "$AOI_FIGURE" \
    --color-levels="$COLOR_LEVELS" \
    --linthresh "$LINTHRESH" \
    --linear-frac "$LINEAR_FRAC" \
    --dpi "$DPI" --regional-height "$REGIONAL_HEIGHT" --aoi-height "$AOI_HEIGHT"

printf '\n[STEP 2/2] Figures generated from the retained run; CaMa-Flood was not rerun.\n'
printf '\n[SUCCESS] Created Tutorial 11 Figures 15a and 15b.\n'
printf 'Regional: %s\nAOI: %s\nAnalysis data: %s\n' \
    "$REGIONAL_FIGURE" "$AOI_FIGURE" "$ANALYSIS_FILE"
