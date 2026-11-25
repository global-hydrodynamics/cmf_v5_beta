#!/bin/bash
# Convert the sample Binary maps created by script_params/s06 to NetCDF.
set -eu

VARIANTS=(
    "subbsn-sample.bin:subbsn.bin"
    "subcol-sample.bin:subcol.bin"
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
[ "$MAP_DIR" != "$REPO_ROOT/map/tools" ] || { echo 'ERROR: map/tools/script_format_conv is a template, not a map; supply --map-dir.' >&2; exit 2; }
[ -f "$MAP_DIR/params.txt" ] || { echo "ERROR: params.txt not found in $MAP_DIR" >&2; exit 1; }

CONVERTER="$REPO_ROOT/map/tools/code/convert_map_binary_to_netcdf.py"
REGISTRY="$REPO_ROOT/variable_table/map_variables.csv"
for VARIANT in "${VARIANTS[@]}"; do
    INPUT=${VARIANT%%:*}
    [ -f "$MAP_DIR/binary/$INPUT" ] || { echo "ERROR: Binary sample not found: $MAP_DIR/binary/$INPUT" >&2; exit 1; }
done
CONVERTED=0
SKIPPED=0
for VARIANT in "${VARIANTS[@]}"; do
    INPUT=${VARIANT%%:*}
    REFERENCE=${VARIANT#*:}
    [ "$INPUT" != "$REFERENCE" ] || { echo "ERROR: invalid variant mapping: $VARIANT" >&2; exit 2; }
    SOURCE="$MAP_DIR/binary/$INPUT"
    OUTPUT="$MAP_DIR/${INPUT%.bin}.nc"
    [ -f "$SOURCE" ] || { echo "ERROR: Binary sample not found: $SOURCE" >&2; exit 1; }
    if [ -f "$OUTPUT" ] && [ "$NO_OVERWRITE" -eq 1 ]; then
        printf 'Existing output preserved: %s\n' "$OUTPUT"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    printf '%s -> %s\n' "$SOURCE" "$OUTPUT"
    python3 "$CONVERTER" --map-dir "$MAP_DIR" --input "$SOURCE" \
        --output "$OUTPUT" --reference-binary "$REFERENCE" \
        --registry "$REGISTRY"
    CONVERTED=$((CONVERTED + 1))
done
printf 'Converted: %s; skipped: %s\n' "$CONVERTED" "$SKIPPED"
