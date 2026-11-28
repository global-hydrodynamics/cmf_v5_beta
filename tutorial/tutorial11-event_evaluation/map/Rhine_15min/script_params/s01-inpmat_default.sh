#!/bin/sh
set -eu

# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
# Standard global 1-degree ELSE_GPCC runoff input grid.
ROFFTAG="test-1deg"  # Runoff dataset/grid identifier.
GRSIZEIN=1.0         # Input runoff grid resolution [degree].
WESTIN=-180.0        # Input runoff grid western boundary [degree].
EASTIN=180.0         # Input runoff grid eastern boundary [degree].
NORTHIN=90.0         # Input runoff grid northern boundary [degree].
SOUTHIN=-90.0        # Input runoff grid southern boundary [degree].
OLAT="NtoS"          # Input runoff grid latitude ordering (north to south).
HIRES_TAG=""         # Empty recommends the coarsest available high-res map.
# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"

cmf_check_init "Generate the standard runoff input matrix"

HIRES_TAG=$(cmf_select_hires_tag "$HIRES_TAG")  # Select high-res map (e.g., 1min, 15sec, 3sec).

cmf_check_step 1 1 "Map river cells to the configured runoff grid"
"$PYTHON_CMD" "$CODE_DIR/param_inpmat_generate.py" "$HIRES_TAG" "$GRSIZEIN" \
    "$WESTIN" "$EASTIN" "$NORTHIN" "$SOUTHIN" "$OLAT" \
    "diminfo_${ROFFTAG}.nml" "inpmat_${ROFFTAG}.nc" --map-dir ..

cmf_check_success

# Optional Python CLI flags: add --map-format binary to use legacy Binary maps.
