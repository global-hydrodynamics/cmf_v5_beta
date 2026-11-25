#!/bin/sh
set -eu

# CaMa-Flood general setting (check CMF root, import shell error checker)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
# Standard global 1-degree ELSE_GPCC runoff grid.
ROFFTAG="test-1deg"
GRSIZEIN=1.0
WESTIN=-180.0
EASTIN=180.0
NORTHIN=90.0
SOUTHIN=-90.0
OLAT="NtoS"
HIRES_TAG=""  # Empty selects the coarsest installed map; set a tag to choose explicitly.
# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
cmf_check_init "Generate the standard runoff input matrix"

HIRES_TAG=$(cmf_select_hires_tag "$HIRES_TAG")

cmf_check_step 1 1 "Map river cells to the configured runoff grid"
"$PYTHON_CMD" "$CODE_DIR/param_inpmat_generate.py" "$HIRES_TAG" "$GRSIZEIN" \
    "$WESTIN" "$EASTIN" "$NORTHIN" "$SOUTHIN" "$OLAT" \
    "diminfo_${ROFFTAG}.txt" "inpmat_${ROFFTAG}.nc" --map-dir ..
cmf_check_success

# Optional Python CLI flags: add --map-format binary to use legacy Binary maps.
