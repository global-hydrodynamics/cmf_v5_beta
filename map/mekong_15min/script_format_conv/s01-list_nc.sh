#!/bin/sh
# List registered base-map NetCDF rasters for s02-nc2bin.sh.
set -eu

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
REPO_ROOT=$(CDPATH= cd "$SCRIPT_DIR/../../.." && pwd -P)
RUN_DIR=$(pwd -P)
MAP_DIR=""
OUTPUT="$RUN_DIR/nc2bin_list.txt"

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
[ -f "$MAP_DIR/params.txt" ] || { echo "ERROR: params.txt not found in $MAP_DIR" >&2; exit 1; }

python3 "$REPO_ROOT/map/tools/code/list_map_conversion_sources.py" \
    --map-dir "$MAP_DIR" --format netcdf --output "$OUTPUT"
