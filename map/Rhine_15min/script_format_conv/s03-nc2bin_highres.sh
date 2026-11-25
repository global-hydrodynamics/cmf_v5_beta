#!/bin/sh
# Convert registered high-resolution NetCDF products to Binary.
# Run from this map's script_format_conv/ directory.
set -eu

# CaMa-Flood general setting (check CMF root, import shell error checker)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/code/cmf_check_shell_error.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
HIRES=""       # Empty selects the coarsest installed NetCDF resolution.
VARS="all"    # Use all registered products or list selected file stems.
JOBS=8         # Maximum parallel conversion workers.

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
REGISTRY="$CMF_V50_ROOT/variable_table/map_variables.csv"
cmf_check_init "Convert high-resolution NetCDF map products"
if [ -z "$HIRES" ]; then
    for tag in 1min 30sec 15sec 5sec 3sec 1sec; do
        if [ -f "../$tag/location.txt" ]; then HIRES=$tag; break; fi
    done
fi
[ -n "$HIRES" ] || { printf 'No NetCDF high-resolution location.txt found in the map root.\n' >&2; exit 1; }
cmf_check_step 1 1 "Convert registered high-resolution products for $HIRES"
"$PYTHON_CMD" "$CODE_DIR/convert_highres_netcdf_to_binary.py" \
    --map-dir .. --hires "$HIRES" --variables "$VARS" \
    --registry "$REGISTRY" --jobs "$JOBS"
cmf_check_success

# Optional converter flags: --no-overwrite, --force, --map-format binary.
