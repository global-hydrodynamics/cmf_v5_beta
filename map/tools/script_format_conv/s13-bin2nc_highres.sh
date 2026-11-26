#!/bin/sh
# Convert registered high-resolution Binary map tiles to NetCDF.
# Run from this map's script_format_conv/ directory.
set -eu

# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
HIRES=""       # Empty prompts for one or more available high-res maps.
VARS="all"     # All registered variables, or space-separated file stems.
JOBS=8         # Maximum parallel conversion workers.
COMPRESSION_LEVEL=3

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
REGISTRY="$CMF_V50_ROOT/variable_table/map_variables.csv"
cmf_check_init "Convert high-resolution Binary map products"
HIRES=$(cmf_select_hires_for_conversion bin2nc "$HIRES")
[ -n "$HIRES" ] || exit 0  # User cancelled before conversion.
cmf_check_step 1 1 "Convert registered high-resolution products for $HIRES"
"$PYTHON_CMD" "$CODE_DIR/convert_highres_binary_to_netcdf.py" \
    --map-dir .. --hires "$HIRES" --variables "$VARS" \
    --registry "$REGISTRY" --compression-level "$COMPRESSION_LEVEL" --jobs "$JOBS" "$@"
cmf_check_success

# Optional converter flags: --no-overwrite, --force. Default replaces NetCDF outputs.
