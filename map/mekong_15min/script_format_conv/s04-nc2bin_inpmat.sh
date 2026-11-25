#!/bin/sh
# Convert the selected runoff input matrix from NetCDF to Binary.
# Run from this map's script_format_conv/ directory.
set -eu

# CaMa-Flood general setting (check CMF root, import shell error checker)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/code/cmf_check_shell_error.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
ROFFTAG="test-1deg"  # Select the paired inpmat and diminfo filenames.

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
REGISTRY="$CMF_V50_ROOT/variable_table/map_variables.csv"
SOURCE="../inpmat_${ROFFTAG}.nc"
DIMINFO="../diminfo_${ROFFTAG}.txt"
OUTPUT="../binary/inpmat_${ROFFTAG}.bin"
cmf_check_init "Convert runoff input matrix to Binary"
[ -f "$SOURCE" ] || { printf 'INPMAT source missing: %s\n' "$SOURCE" >&2; exit 1; }
[ -f "$DIMINFO" ] || { printf 'Paired diminfo missing: %s\n' "$DIMINFO" >&2; exit 1; }
mkdir -p ../binary
cmf_check_step 1 1 "Convert the three-variable runoff input matrix"
"$PYTHON_CMD" "$CODE_DIR/convert_inpmat.py" \
    netcdf-to-binary --input "$SOURCE" --output "$OUTPUT" --diminfo "$DIMINFO"
# The Binary-side descriptor must name the Binary file; keep the NetCDF-side file unchanged.
awk -v binary="inpmat_${ROFFTAG}.bin" 'NR == 7 { $0 = binary } { print }' \
    "$DIMINFO" > "../binary/diminfo_${ROFFTAG}.txt"
cmf_check_success
