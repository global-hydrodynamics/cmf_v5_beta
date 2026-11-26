#!/bin/sh
# Generate the Mekong regional 1-degree runoff input matrix.
# Run from this map's script_params/ directory.
set -eu

# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
ROFFTAG="repo-mek_1deg"  # Runoff dataset/grid identifier.
GRSIZEIN=1                 # Input runoff grid resolution [degree].
WESTIN=90                  # Input runoff grid western boundary [degree].
EASTIN=110                 # Input runoff grid eastern boundary [degree].
NORTHIN=35                 # Input runoff grid northern boundary [degree].
SOUTHIN=5                  # Input runoff grid southern boundary [degree].
OLAT="NtoS"               # Input runoff grid latitude ordering (north to south).
HIRES_TAG="1min"          # High-resolution source map used for grid overlap.

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"

cmf_check_init "Generate Mekong regional runoff input matrix"

cmf_check_step 1 1 "Map river cells to the regional 1-degree runoff grid"
"$PYTHON_CMD" "$CODE_DIR/param_inpmat_generate.py" "$HIRES_TAG" "$GRSIZEIN" \
    "$WESTIN" "$EASTIN" "$NORTHIN" "$SOUTHIN" "$OLAT" \
    "diminfo_${ROFFTAG}.txt" "inpmat_${ROFFTAG}.bin" --map-dir .. --map-format binary

cmf_check_success

# Optional Python CLI flag: omit --map-format binary to use standard NetCDF output.
