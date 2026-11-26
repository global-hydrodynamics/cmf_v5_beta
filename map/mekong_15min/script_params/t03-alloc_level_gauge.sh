#!/bin/sh
set -eu

# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
GAUGE_IN="../../data/MLIT_LevelGauge_allocated.csv"  # MERIT Hydro-preallocated level-gauge table.
HIRES_TAG=""                                     # Empty selects the coarsest installed NetCDF resolution.
# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
cmf_check_init "Allocate MLIT water-level gauges to CaMa-Flood catchments"
HIRES_TAG=$(cmf_select_hires_tag "$HIRES_TAG" --single-area)  # Select a single-area high-res map.
cmf_check_step 1 1 "Allocate MLIT level gauges using the $HIRES_TAG map"
"$PYTHON_CMD" "$CODE_DIR/allocate_level_gauge.py" "$GAUGE_IN" "$HIRES_TAG" \
    --map-dir .. --output-dir ..
cmf_check_success

# Optional Python CLI flag: add --map-format binary for a legacy Binary map.
