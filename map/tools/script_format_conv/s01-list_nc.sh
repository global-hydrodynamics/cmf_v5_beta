#!/bin/sh
# Write the registered base-map NetCDF conversion list in this directory.
# Run from this map's script_format_conv/ directory.
set -eu

# CaMa-Flood general setting (check CMF root, import shell error checker)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
OUTPUT="nc2bin_list.txt"

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
REGISTRY="$CMF_V50_ROOT/variable_table/map_variables.csv"
cmf_check_init "List registered NetCDF map inputs"
cmf_check_step 1 1 "Create the local NetCDF-to-Binary conversion list"
"$PYTHON_CMD" "$CODE_DIR/list_map_conversion_sources.py" \
    --map-dir .. --format netcdf --output "$OUTPUT"
cmf_check_success
