#!/bin/sh
# Combine individual NetCDF maps into legacy consolidated containers.
# Run from the target map's script_format_conv/ directory.
# Write rivclim.nc and rivpar.nc in the selected map directory.
set -eu

# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
MAP_DIR="../"               # Parent directory containing the target map.
NEXTXY="nextxy.nc"          # Include regional-boundary connections.
RIVWTH="rivwth_merit.nc"      # Alternative: rivwth.nc (empirical channel width).

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
REGISTRY="$CMF_V50_ROOT/variable_table/map_variables.csv"

cmf_check_init "Create legacy consolidated NetCDF maps"

cmf_check_step 1 1 "Combine the selected connectivity and channel-width maps"
"$PYTHON_CMD" "$CODE_DIR/create_legacy_netcdf_map.py" --map-dir "$MAP_DIR" \
    --nextxy "$NEXTXY" --rivwth "$RIVWTH" --force

cmf_check_success
