#!/bin/bash
# Convert the sample maps produced by script_params/s06 to Binary.
# Run from this map's script_format_conv/ directory.
set -eu

# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
VARIANTS=(
    "subbsn-sample.nc:subbsn.bin"
    "subcol-sample.nc:subcol.bin"
)
NO_OVERWRITE=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --no-overwrite) NO_OVERWRITE=1; shift ;;
        --help|-h) printf 'Usage: ./%s [--no-overwrite]\n' "${0##*/}"; exit 0 ;;
        *) printf 'Usage: ./%s [--no-overwrite]\n' "${0##*/}" >&2; exit 2 ;;
    esac
done

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
REGISTRY="$CMF_V50_ROOT/variable_table/map_variables.csv"
cmf_check_init "Convert sample NetCDF maps to Binary"
BINARY_DIR="../binary"
mkdir -p "$BINARY_DIR"
STAGING_DIR=""
cleanup_exit() {
    EXIT_STATUS=$?
    [ -z "$STAGING_DIR" ] || rm -rf "$STAGING_DIR"
    cmf_check_on_exit "$EXIT_STATUS"
}
trap cleanup_exit 0
STAGING_DIR=$(mktemp -d "$BINARY_DIR/.sample-nc2bin.XXXXXX")
for VARIANT in "${VARIANTS[@]}"; do
    SOURCE_NAME=${VARIANT%%:*}
    [ -f "../$SOURCE_NAME" ] || { printf 'Sample NetCDF is missing: ../%s\n' "$SOURCE_NAME" >&2; exit 1; }
done

cmf_check_step 1 1 "Convert the sample subbasin and color maps"
CONVERTED=0
SKIPPED=0
for VARIANT in "${VARIANTS[@]}"; do
    SOURCE_NAME=${VARIANT%%:*}
    REFERENCE=${VARIANT#*:}
    SOURCE="../$SOURCE_NAME"
    OUTPUT="$BINARY_DIR/${SOURCE_NAME%.nc}.bin"
    if [ -f "$OUTPUT" ] && [ "$NO_OVERWRITE" -eq 1 ]; then
        printf 'Existing output preserved: %s\n' "$OUTPUT"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi
    STAGED="$STAGING_DIR/$REFERENCE"
    printf '%s -> %s\n' "$SOURCE" "$OUTPUT"
    "$PYTHON_CMD" "$CODE_DIR/convert_map_netcdf_to_binary.py" --map-dir .. \
        --input "$SOURCE" --output "$STAGED" --registry "$REGISTRY" \
        --source-variable "${SOURCE_NAME%.nc}"
    mv -f "$STAGED" "$OUTPUT"
    CONVERTED=$((CONVERTED + 1))
done
printf 'Converted: %s; skipped: %s\n' "$CONVERTED" "$SKIPPED"
cmf_check_success

# Optional shell flag: --no-overwrite preserves existing Binary outputs.
