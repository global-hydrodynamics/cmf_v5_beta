#!/bin/sh
# Generate a map-to-runoff matrix for a regular runoff grid.
# Copy to <map>/script_params/, edit the grid settings, and run from any CWD.
#
# Inputs: params.txt and <HIRES_TAG>/location.txt with each area's catmxy.bin.
# Outputs: diminfo_<ROFFTAG>.txt and inpmat_<ROFFTAG>.bin in the map root.
set -eu

# Paths
# Command substitution stores the resolved path; CDPATH= keeps cd output predictable.
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
MAP_DIR=$(CDPATH= cd "$SCRIPT_DIR/.." && pwd -P)
CODE_DIR=$(CDPATH= cd "$SCRIPT_DIR/../../tools/code" && pwd -P)

# Runoff input grid: ERA5-Land global 0.1-degree grid, independent of the model map.
# ERA5land_global labels the spatial grid, not the repo-ERA5land-glb_2day period.
# Reuse this grid tag for longer ERA5-Land series with identical coordinates/order;
# generate a separate matrix in each target CaMa-Flood map.
ROFFTAG="ERA5land_global"  # User-editable runoff-grid tag for the paired output filenames.
GRSIZEIN=0.1              # Runoff grid-cell size (degrees).
WESTIN=-180.05            # Western edge: first longitude center (-180) minus half a cell.
EASTIN=179.95             # Eastern edge: last longitude center (179.9) plus half a cell.
NORTHIN=90.05             # Northern edge: first latitude center (90) plus half a cell.
SOUTHIN=-90.05            # Southern edge: last latitude center (-90) minus half a cell.
OLAT="NtoS"               # Runoff latitude row order: NtoS or StoN.

# High-resolution map selection is independent of the runoff-grid tag.
HIRES_TAG=""  # Map directory tag; empty selects an available 1min or 15sec grid.

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------

# ${0##*/} removes the directory portion of the script path for readable messages.
SCRIPT_NAME=${0##*/}
STEP="Select high-resolution map input"
# The exit trap reports failures and preserves status; signal traps use standard nonzero statuses.
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

# Select the map-resolution input automatically when HIRES_TAG is not set.
if [ -z "$HIRES_TAG" ]; then
    if [ -f "$MAP_DIR/1min/location.txt" ]; then
        HIRES_TAG=1min
    elif [ -f "$MAP_DIR/15sec/location.txt" ]; then
        HIRES_TAG=15sec
    else
        echo "Set HIRES_TAG to an available map directory (expected 1min or 15sec)." >&2
        exit 1
    fi
fi

DIMINFO="diminfo_${ROFFTAG}.txt"
INPMAT="inpmat_${ROFFTAG}.bin"

EXEC_INPMAT="$CODE_DIR/param_inpmat_generate"

# For each river cell, find its runoff-grid source cell and write the matrix and descriptor.
cd "$MAP_DIR"

STEP="Map river cells to the configured runoff grid"
printf '\n==================================================\n[STEP 1/1] Generate runoff input matrix\n==================================================\n\n'
"$EXEC_INPMAT" "$HIRES_TAG" "$GRSIZEIN" "$WESTIN" "$EASTIN" \
    "$NORTHIN" "$SOUTHIN" "$OLAT" "$DIMINFO" "$INPMAT"

printf '\n==================================================\n[SUCCESS] %s\n==================================================\n' "$SCRIPT_NAME"
