#!/bin/sh
# Restore legacy-compatible Binary tiles from the authoritative high-resolution NetCDF.
# Run from <map>/script_format_conv/ or select an external map with --map-dir PATH.
set -eu

# User settings: select available high-resolution directories and variables.
# Choose one or more available high-resolution map directories.
# Each <HIRES>_nc/ must contain location.txt and registered NetCDF tile files.
#HIRES="1min 15sec 3sec"
HIRES="1min"

# Choose registered file stems present in the selected NetCDF directories.
# Options shown here are high-resolution registry products; a map need not
# contain every one of them. Multi-record files (catmxy, downxy) are converted
# with all their registered records together.
#VARS="catmxy catmz100 catmzz downxy elevtn flddif flwdir grdare hand rivwth uparea visual"
VARS="catmxy downxy elevtn uparea hand flddif rivwth"

# Maximum number of parallel Python worker processes.
JOBS=8

# Existing Binary outputs are skipped by default. Pass --force to replace them.
FORCE=0

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------

# Command substitution locates shared resources independently of the target map.
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
REPO_ROOT=$(CDPATH= cd "$SCRIPT_DIR/../../.." && pwd -P)
TOOL_DIR="$REPO_ROOT/map/tools/code"
REGISTRY="$REPO_ROOT/variable_table/map_variables.csv"
CONVERTER="$TOOL_DIR/convert_highres_netcdf_to_binary.py"
# The physical current directory owns the list and supplies the implicit target.
RUN_DIR=$(pwd -P)
MAP_DIR=""

SCRIPT_NAME=${0##*/}
STEP="Validate high-resolution restoration settings"
# Print a stage-specific error when any command exits unsuccessfully.
trap '
    EXIT_STATUS=$?
    trap - 0
    if [ "$EXIT_STATUS" -ne 0 ]; then
        printf "\n[ERROR] %s failed during: %s (exit %s)\n" "$SCRIPT_NAME" "$STEP" "$EXIT_STATUS" >&2
    fi
    exit "$EXIT_STATUS"
' 0
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

# --map-dir is explicit; otherwise require a map-local script_format_conv/ current directory.
while [ "$#" -gt 0 ]; do
    case "$1" in
        --map-dir)
            if [ "$#" -lt 2 ] || [ -z "$2" ]; then
                printf 'ERROR: --map-dir requires a directory.\n' >&2
                exit 2
            fi
            MAP_DIR=$2
            shift 2
            ;;
        --force) FORCE=1; shift ;;
        --help|-h)
            printf 'Usage: %s [--map-dir PATH] [--force]\n' "$SCRIPT_NAME"
            exit 0
            ;;
        *)
            printf 'Usage: %s [--map-dir PATH] [--force]\n' "$SCRIPT_NAME" >&2
            exit 2
            ;;
    esac
done

if [ -z "$MAP_DIR" ]; then
    # Shell suffix removal gives the last directory component without invoking basename.
    if [ "${RUN_DIR##*/}" != script_format_conv ]; then
        printf 'ERROR: run from <map>/script_format_conv/ or supply --map-dir PATH.\n' >&2
        exit 2
    fi
    MAP_DIR="$RUN_DIR/.."
fi
if [ ! -d "$MAP_DIR" ]; then
    printf 'ERROR: map directory does not exist: %s\n' "$MAP_DIR" >&2
    exit 1
fi
MAP_DIR=$(CDPATH= cd "$MAP_DIR" && pwd -P)
if [ "$MAP_DIR" = "$REPO_ROOT/map/tools" ]; then
    printf 'ERROR: map/tools/script_format_conv is a template, not a map. Run from a map-local directory or supply --map-dir PATH.\n' >&2
    exit 2
fi
if [ ! -f "$MAP_DIR/params.txt" ]; then
    printf 'ERROR: target is not a map directory (params.txt missing): %s\n' "$MAP_DIR" >&2
    exit 1
fi

if [ ! -f "$CONVERTER" ] || [ ! -f "$REGISTRY" ]; then
    printf 'ERROR: converter not found: %s\n' "$CONVERTER" >&2
    exit 1
fi

STEP="Restore selected high-resolution Binary tiles"
printf '\n[STEP 1/1] Restore Binary working files from distribution NetCDF\n'
printf 'Map: %s\nHigh-resolution directories: %s\nVariables: %s\nWorkers: %s\n' \
    "$MAP_DIR" "$HIRES" "$VARS" "$JOBS"

# Python validates coordinates, restores location.txt safely and writes each Binary atomically.
for re in $HIRES; do
    if [ "$FORCE" -eq 1 ]; then
        python3 "$CONVERTER" --map-dir "$MAP_DIR" --hires "$re" --variables "$VARS" \
            --registry "$REGISTRY" --jobs "$JOBS" --force
    else
        python3 "$CONVERTER" --map-dir "$MAP_DIR" --hires "$re" --variables "$VARS" \
            --registry "$REGISTRY" --jobs "$JOBS"
    fi
done

printf '\n[SUCCESS] High-resolution Binary working files restored.\n'
