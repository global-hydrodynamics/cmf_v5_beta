#!/bin/sh
# Restore registered high-resolution Binary tiles from NetCDF.
set -eu

# User settings: blank selects the first available NetCDF resolution.
HIRES=""
VARS="all"
JOBS=8
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
if [ -z "$HIRES" ]; then
    for tag in 1min 30sec 15sec 5sec 3sec 1sec; do
        if [ -f "$MAP_DIR/$tag/location.txt" ]; then HIRES=$tag; break; fi
    done
fi
[ -n "$HIRES" ] || { echo "ERROR: no NetCDF high-resolution location.txt found in $MAP_DIR" >&2; exit 1; }

set -- --map-dir "$MAP_DIR" --hires "$HIRES" --variables "$VARS" \
    --registry "$REPO_ROOT/variable_table/map_variables.csv" --jobs "$JOBS"
[ "$NO_OVERWRITE" -eq 0 ] || set -- "$@" --no-overwrite
python3 "$REPO_ROOT/map/tools/code/convert_highres_netcdf_to_binary.py" "$@"
