#!/bin/sh
set -eu

# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
HIRES_TAG=""  # Empty selects the coarsest installed resolution; set explicitly if needed.
# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"

cmf_check_init "Estimate permanent-water area"

HIRES_TAG=$(cmf_select_hires_tag "$HIRES_TAG")  # Select high-res map (e.g., 1min, 15sec, 3sec).

cmf_check_step 1 1 "Aggregate permanent-water area from the selected high-resolution map"
"$PYTHON_CMD" "$CODE_DIR/param_water_calc_prmwat.py" "$HIRES_TAG" --map-dir ..

cmf_check_success

# Optional Python CLI flags: add --map-format binary to use legacy Binary maps.
