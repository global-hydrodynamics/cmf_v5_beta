#!/bin/sh
# Map GRanD reservoirs from MERIT Hydro to CaMa-Flood unit catchments.
# Inputs: GRanD_allocated.csv, params.txt, uparea.bin, ctmare.bin, nextxy.bin, and selected HIRES_TAG files.
# Outputs: GRanD_river.txt, GRanD_small.txt, and GRanD_error.txt in the map root.
set -eu

# Paths
# Command substitution stores the resolved path; CDPATH= keeps cd output predictable.
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
PYTHON_CMD="${PYTHON_CMD:-python3}"
MAP_FORMAT="${MAP_FORMAT:-netcdf}"  # Set binary only for legacy Binary maps.
if [ -n "${CMF5_ROOT:-}" ]; then
    CODE_DIR="$CMF5_ROOT/map/tools/code"
else
    CODE_DIR="$SCRIPT_DIR/../../tools/code"
fi
if [ ! -d "$CODE_DIR" ]; then
    printf '[ERROR] Shared Python tools not found: %s (set CMF5_ROOT to the repository root)\n' "$CODE_DIR" >&2
    exit 1
fi
MAP_DIR=$(CDPATH= cd "$SCRIPT_DIR/.." && pwd -P)

# Dam allocation input and map-root output tables; input path is relative to script_params/.
DAM_IN="../../data/GRanD_allocated.csv"   # MERIT Hydro-preallocated GRanD reservoir table.
DAM_RIVER_OUT="$MAP_DIR/GRanD_river.txt"  # Output table for dams mapped to the river network.
DAM_SMALL_OUT="$MAP_DIR/GRanD_small.txt"  # Output table for dams classified as small by the legacy rule.
DAM_ERROR_OUT="$MAP_DIR/GRanD_error.txt"  # Output table for dams that could not be mapped.
HIRES_TAG=""  # Auto-select the coarsest available grid for domain-wide allocation.

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------

# ${0##*/} removes the directory portion of the script path for readable messages.
SCRIPT_NAME=${0##*/}
STEP="Prepare dam-allocation workflow"
# The exit trap reports the failed stage and preserves the original command status.
trap '
    EXIT_STATUS=$?
    trap - 0
    if [ "$EXIT_STATUS" -ne 0 ]; then
        printf "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n" >&2
        printf "!!! ERROR: %s FAILED !!!\n" "$SCRIPT_NAME" >&2
        printf "!!! Step: %s\n" "$STEP" >&2
        printf "!!! Exit status: %s\n" "$EXIT_STATUS" >&2
        printf "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n" >&2
    fi
    exit "$EXIT_STATUS"
' 0
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

# ----------------------------------------------------------------------
# End of error handling.
# ----------------------------------------------------------------------

# Prefer the coarsest installed NetCDF grid; the data consumer validates its contents.
AVAILABLE=""
for tag in 1min 30sec 15sec 5sec 3sec 1sec; do
    if [ -d "$MAP_DIR/$tag" ]; then
        AVAILABLE="${AVAILABLE}${AVAILABLE:+ }$tag"
        if [ -z "$HIRES_TAG" ]; then HIRES_TAG=$tag; fi
    fi
done
if [ -z "$HIRES_TAG" ]; then
    printf 'ERROR: No NetCDF high-resolution directory found in %s.\n' "$MAP_DIR" >&2
    exit 1
fi
printf 'Allocation high-resolution map: %s/%s\n' "$MAP_DIR" "$HIRES_TAG"

EXEC_ALLOCATE="$CODE_DIR/allocate_dam.py"

cd "$SCRIPT_DIR"

STEP="Allocate dams and separate river, small, and error records"
printf '\n==================================================\n[STEP 1/2] Allocate dams (%s)\n==================================================\n\n' "$HIRES_TAG"
"$PYTHON_CMD" "$EXEC_ALLOCATE" "$DAM_IN" "$HIRES_TAG" --map-format "$MAP_FORMAT"

STEP="Move allocated dam tables into the map root"
printf '\n==================================================\n[STEP 2/2] Save GRanD allocation tables\n==================================================\n\n'
mv ./dam_alloc_river.txt "$DAM_RIVER_OUT"
mv ./dam_alloc_small.txt "$DAM_SMALL_OUT"
mv ./dam_alloc_error.txt "$DAM_ERROR_OUT"

printf '\n==================================================\n[SUCCESS] %s\n==================================================\n' "$SCRIPT_NAME"
