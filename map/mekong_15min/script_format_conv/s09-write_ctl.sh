#!/bin/sh
# Generate registered GrADS CTLs beside Binary products.
set -eu

PYTHON_CMD="${PYTHON_CMD:-python3}"
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
REPO_ROOT=$(CDPATH= cd "$SCRIPT_DIR/../../.." && pwd -P)
RUN_DIR=$(pwd -P)
MAP_DIR=""
OPTIONS=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --map-dir) [ "$#" -ge 2 ] || { echo 'ERROR: --map-dir requires a path.' >&2; exit 2; }; MAP_DIR=$2; shift 2 ;;
        --dry-run|--no-overwrite|--overwrite) OPTIONS="$OPTIONS $1"; shift ;;
        --help|-h) echo "Usage: ${0##*/} [--map-dir PATH] [--dry-run] [--no-overwrite]"; exit 0 ;;
        *) echo "Usage: ${0##*/} [--map-dir PATH] [--dry-run] [--no-overwrite]" >&2; exit 2 ;;
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
cp "$MAP_DIR/params.txt" "$BINARY_DIR/params.txt"
for DIMINFO in "$MAP_DIR"/diminfo_*.txt; do
    [ -f "$DIMINFO" ] || continue
    [ -f "$BINARY_DIR/${DIMINFO##*/}" ] || cp "$DIMINFO" "$BINARY_DIR/${DIMINFO##*/}"
done
for SOURCE_LOCATION in "$MAP_DIR"/*/location.txt; do
    [ -f "$SOURCE_LOCATION" ] || continue
    RESOLUTION_DIR=${SOURCE_LOCATION%/location.txt}
    RESOLUTION=${RESOLUTION_DIR##*/}
    mkdir -p "$BINARY_DIR/$RESOLUTION"
    cp "$SOURCE_LOCATION" "$BINARY_DIR/$RESOLUTION/location.txt"
done
GENERATOR="$REPO_ROOT/map/tools/code/generate_ctl.py"

# Word splitting intentionally expands the parsed generator flags.
set -- $OPTIONS
"$PYTHON_CMD" "$GENERATOR" --map-dir "$BINARY_DIR" "$@"

for LOCATION in "$BINARY_DIR"/*/location.txt; do
    [ -f "$LOCATION" ] || continue
    GRID_DIR=${LOCATION%/location.txt}
    RESOLUTION=${GRID_DIR##*/}
    SOURCE_LOCATION="$MAP_DIR/$RESOLUTION/location.txt"
    [ -f "$SOURCE_LOCATION" ] && cp "$SOURCE_LOCATION" "$LOCATION"
    "$PYTHON_CMD" "$GENERATOR" --map-dir "$GRID_DIR" $OPTIONS
done

# Preserve CTL definitions for sample and station variants whose filenames
# intentionally differ from the canonical registry names.
for ENTRY in \
    "subbsn-sample.bin:subbsn.bin" \
    "subcol-sample.bin:subcol.bin" \
    "upbasin-*.bin:upbasin.bin"; do
    PATTERN=${ENTRY%%:*}
    REFERENCE=${ENTRY#*:}
    for BINARY in "$BINARY_DIR"/$PATTERN; do
        [ -f "$BINARY" ] || continue
        "$PYTHON_CMD" "$GENERATOR" --map-dir "$BINARY_DIR" \
            --input "${BINARY##*/}" --reference-binary "$REFERENCE" $OPTIONS
    done
done
