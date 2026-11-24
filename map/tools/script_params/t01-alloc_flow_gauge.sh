#!/bin/sh
# Map GRDC flow gauges from MERIT Hydro to CaMa-Flood unit catchments.
# Inputs: GRDC_allocated.csv, params.txt, uparea.bin, nextxy.bin, and selected HIRES_TAG files.
# Output: GRDC_alloc.txt in the map root.
set -eu

# Paths
# Command substitution stores the resolved path; CDPATH= keeps cd output predictable.
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
PYTHON_CMD="${PYTHON_CMD:-python3}"
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

# Flow-gauge allocation inputs and outputs; input path is relative to script_params/.
GAUGE_IN="../../data/GRDC_allocated.csv"  # MERIT Hydro-preallocated GRDC station table.
GAUGE_OUT="$MAP_DIR/GRDC_alloc.txt"       # CaMa-Flood allocation table written in the map root.
GAUGE_MODE="multi"                        # Allocation mode: multi or single.
HIRES_TAG=""  # Auto-select the coarsest available grid for domain-wide allocation.

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------

# ${0##*/} removes the directory portion of the script path for readable messages.
SCRIPT_NAME=${0##*/}
STEP="Prepare flow-gauge allocation"
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

# Prefer the coarsest installed Binary grid; the data consumer validates its contents.
AVAILABLE=""
for tag in 1min 30sec 15sec 5sec 3sec 1sec; do
    if [ -d "$MAP_DIR/$tag" ]; then
        AVAILABLE="${AVAILABLE}${AVAILABLE:+ }$tag"
        if [ -z "$HIRES_TAG" ]; then HIRES_TAG=$tag; fi
    fi
done
if [ -z "$HIRES_TAG" ]; then
    printf 'ERROR: No Binary high-resolution directory found in %s.\n' "$MAP_DIR" >&2
    exit 1
fi
printf 'Allocation high-resolution map: %s/%s\n' "$MAP_DIR" "$HIRES_TAG"

EXEC_ALLOCATE="$CODE_DIR/allocate_flow_gauge.py"

cd "$SCRIPT_DIR"

STEP="Allocate gauges to the CaMa-Flood river network"
printf '\n==================================================\n[STEP 1/2] Allocate flow gauges (%s, %s)\n==================================================\n\n' "$GAUGE_MODE" "$HIRES_TAG"
"$PYTHON_CMD" "$EXEC_ALLOCATE" "$GAUGE_IN" "$GAUGE_MODE" "$HIRES_TAG"

STEP="Move allocated flow-gauge table into the map root"
printf '\n==================================================\n[STEP 2/2] Save GRDC_alloc.txt\n==================================================\n\n'
mv ./gauge_alloc.txt "$GAUGE_OUT"

printf '\n==================================================\n[SUCCESS] %s\n==================================================\n' "$SCRIPT_NAME"
