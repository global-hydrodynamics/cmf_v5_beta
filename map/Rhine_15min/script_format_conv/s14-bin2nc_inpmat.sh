#!/bin/sh
# Convert the selected runoff input matrix from Binary to NetCDF.
# Run from this map's script_format_conv/ directory.
set -eu

# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
ROFFTAG="test-1deg"  # Select the paired Binary inpmat and diminfo files.

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
REGISTRY="$CMF_V50_ROOT/variable_table/map_variables.csv"
SOURCE="../binary/inpmat_${ROFFTAG}.bin"
DIMINFO="../binary/diminfo_${ROFFTAG}.txt"
OUTPUT="../inpmat_${ROFFTAG}.nc"

cmf_check_init "Convert runoff input matrix to NetCDF"
[ -f "$SOURCE" ] || { printf 'Binary INPMAT missing: %s\n' "$SOURCE" >&2; exit 1; }
[ -f "$DIMINFO" ] || { printf 'Paired Binary diminfo missing: %s\n' "$DIMINFO" >&2; exit 1; }

cmf_check_step 1 1 "Convert the three-variable runoff input matrix"
"$PYTHON_CMD" "$CODE_DIR/convert_inpmat.py" \
    binary-to-netcdf --input "$SOURCE" --output "$OUTPUT" --diminfo "$DIMINFO"
# The map-root descriptor belongs to the NetCDF product; the Binary-side pair remains in binary/.

cmf_check_success
