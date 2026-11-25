#!/bin/bash
# Convert the sample NetCDF maps created by script_params/s06 to Binary.
set -eu

VARIANTS=(
    "subbsn-sample.nc:subbsn.bin"
    "subcol-sample.nc:subcol.bin"
)
NO_OVERWRITE=0

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
REPO_ROOT=$(CDPATH= cd "$SCRIPT_DIR/../../.." && pwd -P)
RUN_DIR=$(pwd -P)
MAP_DIR=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --map-dir) [ "$#" -ge 2 ] || { echo 'ERROR: --map-dir requires a path.' >&2; exit 2; }; MAP_DIR=$2; shift 2 ;;
        --no-overwrite) NO_OVERWRITE=1; shift ;;
        --help|-h) echo "Usage: ${0##*/} [--map-dir PATH] [--no-overwrite]"; exit 0 ;;
        *) echo "Usage: ${0##*/} [--map-dir PATH] [--no-overwrite]" >&2; exit 2 ;;
    esac
done
if [ -z "$MAP_DIR" ]; then
    [ "${RUN_DIR##*/}" = script_format_conv ] || { echo 'ERROR: run from <map>/script_format_conv/ or pass --map-dir.' >&2; exit 2; }
    MAP_DIR="$RUN_DIR/.."
fi
MAP_DIR=$(CDPATH= cd "$MAP_DIR" && pwd -P)
[ -f "$MAP_DIR/params.txt" ] || { echo "ERROR: params.txt not found in $MAP_DIR" >&2; exit 1; }

BINARY_DIR="$MAP_DIR/binary"
mkdir -p "$BINARY_DIR"
STAGING_DIR=$(mktemp -d "$BINARY_DIR/.sample-nc2bin.XXXXXX")
cleanup() { rm -rf "$STAGING_DIR"; }
trap cleanup EXIT

CONVERTER="$REPO_ROOT/map/tools/code/convert_map_netcdf_to_binary.py"
REGISTRY="$REPO_ROOT/variable_table/map_variables.csv"
for VARIANT in "${VARIANTS[@]}"; do
    SOURCE_NAME=${VARIANT%%:*}
    [ -f "$MAP_DIR/$SOURCE_NAME" ] || { echo "ERROR: NetCDF sample not found: $MAP_DIR/$SOURCE_NAME" >&2; exit 1; }
done
CONVERTED=0
SKIPPED=0
for VARIANT in "${VARIANTS[@]}"; do
    SOURCE_NAME=${VARIANT%%:*}
    REFERENCE=${VARIANT#*:}
    [ "$SOURCE_NAME" != "$REFERENCE" ] || { echo "ERROR: invalid variant mapping: $VARIANT" >&2; exit 2; }
    SOURCE="$MAP_DIR/$SOURCE_NAME"
    OUTPUT="$BINARY_DIR/${SOURCE_NAME%.nc}.bin"
    [ -f "$SOURCE" ] || { echo "ERROR: NetCDF sample not found: $SOURCE" >&2; exit 1; }
    if [ -f "$OUTPUT" ] && [ "$NO_OVERWRITE" -eq 1 ]; then
        printf 'Existing output preserved: %s\n' "$OUTPUT"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    # The converter uses the registered reference filename to select the
    # variable layout; stage under that name so the sample output stays distinct.
    STAGED="$STAGING_DIR/$REFERENCE"
    printf '%s -> %s\n' "$SOURCE" "$OUTPUT"
    python3 "$CONVERTER" --map-dir "$MAP_DIR" --input "$SOURCE" \
        --output "$STAGED" --registry "$REGISTRY" \
        --source-variable "${SOURCE_NAME%.nc}"
    mv -f "$STAGED" "$OUTPUT"
    CONVERTED=$((CONVERTED + 1))
done
printf 'Converted: %s; skipped: %s\n' "$CONVERTED" "$SKIPPED"
