#!/bin/sh
# Generate a map-to-runoff matrix for a regular runoff grid.
# Copy to <map>/script_params/, edit the grid settings, and run from any CWD.
#
# Inputs: params.txt and <HIRES_TAG>/location.txt with each area's catmxy.nc.
# Outputs: diminfo_<ROFFTAG>.txt and inpmat_<ROFFTAG>.nc in the map root.
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
HIRES_TAG=""  # Empty proposes the coarsest installed NetCDF grid; confirm before running.

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

printf 'Selected high-resolution map: %s/%s\n' "$MAP_DIR" "$HIRES_TAG"
while :; do
    printf 'Use this high-resolution map? [Y/n]: '
    IFS= read -r answer
    case "$answer" in
        ""|y|Y|yes|Yes|YES) break ;;
        n|N|no|No|NO)
            while :; do
                printf 'Available resolutions: %s\nChoose resolution: ' "$AVAILABLE"
                IFS= read -r chosen
                for tag in $AVAILABLE; do
                    if [ "$chosen" = "$tag" ]; then
                        HIRES_TAG=$chosen
                        break 2
                    fi
                done
                printf 'Choose one of the listed resolutions.\n'
            done
            break
            ;;
        *) printf 'Please answer Yes or No (Enter = Yes).\n' ;;
    esac
done
printf 'Using high-resolution map: %s/%s\n' "$MAP_DIR" "$HIRES_TAG"

DIMINFO="diminfo_${ROFFTAG}.txt"
INPMAT="inpmat_${ROFFTAG}.nc"

EXEC_INPMAT="$CODE_DIR/param_inpmat_generate.py"

# For each river cell, find its runoff-grid source cell and write the matrix and descriptor.
cd "$MAP_DIR"

STEP="Map river cells to the configured runoff grid"
printf '\n==================================================\n[STEP 1/1] Generate runoff input matrix\n==================================================\n\n'
"$PYTHON_CMD" "$EXEC_INPMAT" "$HIRES_TAG" "$GRSIZEIN" "$WESTIN" "$EASTIN" \
    "$NORTHIN" "$SOUTHIN" "$OLAT" "$DIMINFO" "$INPMAT"

printf '\n==================================================\n[SUCCESS] %s\n==================================================\n' "$SCRIPT_NAME"
