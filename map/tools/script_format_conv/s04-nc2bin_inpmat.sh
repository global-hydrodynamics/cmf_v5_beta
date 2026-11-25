#!/bin/sh
# Restore the dedicated three-variable INPMAT to legacy Binary.
set -eu

# User setting: selects inpmat_<ROFFTAG>.nc and its paired diminfo file.
ROFFTAG="test-1deg"
PYTHON_CMD="${PYTHON_CMD:-python3}"

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
REPO_ROOT=$(CDPATH= cd "$SCRIPT_DIR/../../.." && pwd -P)
RUN_DIR=$(pwd -P)
MAP_DIR=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --map-dir) [ "$#" -ge 2 ] || { echo 'ERROR: --map-dir requires a path.' >&2; exit 2; }; MAP_DIR=$2; shift 2 ;;
        --help|-h) echo "Usage: ${0##*/} [--map-dir PATH]"; exit 0 ;;
        *) echo "Usage: ${0##*/} [--map-dir PATH]" >&2; exit 2 ;;
    esac
done
if [ -z "$MAP_DIR" ]; then
    [ "${RUN_DIR##*/}" = script_format_conv ] || { echo 'ERROR: run from <map>/script_format_conv/ or pass --map-dir.' >&2; exit 2; }
    MAP_DIR="$RUN_DIR/.."
fi
MAP_DIR=$(CDPATH= cd "$MAP_DIR" && pwd -P)
SOURCE="$MAP_DIR/inpmat_${ROFFTAG}.nc"
DIMINFO="$MAP_DIR/diminfo_${ROFFTAG}.txt"
OUTPUT_DIR="$MAP_DIR/binary"
OUTPUT="$OUTPUT_DIR/inpmat_${ROFFTAG}.bin"

[ -f "$SOURCE" ] || { echo "ERROR: INPMAT source not found: $SOURCE" >&2; exit 1; }
[ -f "$DIMINFO" ] || { echo "ERROR: paired diminfo not found: $DIMINFO" >&2; exit 1; }
mkdir -p "$OUTPUT_DIR"
"$PYTHON_CMD" "$REPO_ROOT/map/tools/code/convert_inpmat.py" \
    netcdf-to-binary --input "$SOURCE" --output "$OUTPUT" --diminfo "$DIMINFO"
cp "$DIMINFO" "$OUTPUT_DIR/diminfo_${ROFFTAG}.txt"
