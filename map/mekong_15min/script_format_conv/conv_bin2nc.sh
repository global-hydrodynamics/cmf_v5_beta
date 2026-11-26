#!/bin/sh
# Convert a user-created map Binary file to the registered NetCDF layout.
set -eu

if [ "$#" -ne 2 ]; then
    printf 'Usage: ./conv_bin2nc.sh INPUT.bin REFERENCE\n' >&2
    exit 2
fi

INPUT=$1
REFERENCE=$2
case "$INPUT" in
    */*|"") printf 'INPUT.bin must be a filename in the parent map binary/ directory.\n' >&2; exit 2 ;;
    *.bin) ;;
    *) printf 'INPUT must end in .bin.\n' >&2; exit 2 ;;
esac
case "$REFERENCE" in
    */*|"") printf 'REFERENCE must be a registered filename stem, such as subbsn or nextxy.\n' >&2; exit 2 ;;
esac

: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
PYTHON_CMD=python3
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
REGISTRY="$CMF_V50_ROOT/variable_table/map_variables.csv"
OUTPUT="../${INPUT%.bin}.nc"

printf 'Binary -> NetCDF\n  Input:     ../binary/%s\n  Reference: %s\n  Output:    %s\n' \
    "$INPUT" "$REFERENCE" "$OUTPUT"
"$PYTHON_CMD" "$CODE_DIR/convert_map_binary_to_netcdf.py" --map-dir .. \
    --input "../binary/$INPUT" --output "$OUTPUT" --registry "$REGISTRY" \
    --reference-binary "$REFERENCE.bin"
