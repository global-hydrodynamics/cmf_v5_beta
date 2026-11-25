#!/bin/sh
# Generate bifurcation CSV/NetCDF parameters and standard basin connectivity.
# Copy to <map>/script_params/, configure BIFLAYER and ROFFTAG, and run from any CWD.
#
# Inputs: params.txt, nextxy.nc, basin.nc, bifori.txt, rivhgt.nc,
#         and diminfo_<ROFFTAG>.txt in the map root.
# Outputs: bifprm.csv, bifprm.nc, bifbsn.nc, bifcol.nc; optional check maps.
# Usage: ./s02-bifurcation.sh [check_map]
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

# Bifurcation inputs and runoff-grid matrix selection.
BIFLAYER=5                      # Number of bifori.txt layers to process (1-10).
# test-1deg: global ELSE_GPCC 360 x 180 grid; matrix is specific to this model map.
# Use the same grid tag as s01, which reads map/data/ELSE_GPCC_clm-1981-2010.one.
ROFFTAG="test-1deg"         # Runoff dataset ID used to derive DIMINFO.
DIMINFO="diminfo_${ROFFTAG}.txt"  # Simulation dimension information (model and input grids).
RIVHGT="rivhgt.nc"              # Channel-depth map used to estimate bifurcation depth.
BIFPRM_CSV="bifprm.csv"         # Finalized, named bifurcation parameter table.
BIFPRM_NC="bifprm.nc"           # NetCDF conversion at the map root.

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------

# ${0##*/} removes the directory portion of the script path for readable messages.
SCRIPT_NAME=${0##*/}
STEP="Check optional check_map argument"
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

# Shared Python programs used by this workflow.
EXEC_SETPARAM="$CODE_DIR/param_bif_set_params.py"
EXEC_SETBASIN="$CODE_DIR/param_bif_set_basin.py"
EXEC_CONVERT="$CODE_DIR/convert_bifprm_csv_to_netcdf.py"

# Keep the optional diagnostic switch explicit.
# ${1:-} is empty when no optional check_map argument was supplied.
CHECK_MAP=${1:-}
if [ "$#" -gt 1 ] || { [ -n "$CHECK_MAP" ] && [ "$CHECK_MAP" != check_map ]; }; then
    echo "Usage: $0 [check_map]" >&2
    exit 2
fi

# Keep any existing legacy text table visible; this workflow does not modify it.
if [ -f "$MAP_DIR/bifprm.txt" ]; then
    printf 'WARNING: existing bifprm.txt is a legacy product and will not be changed.\n' >&2
fi

# 1. Filter bifurcation paths by channel width and estimate their bifurcation depth.
cd "$MAP_DIR"

STEP="Filter bifurcation paths and estimate bifurcation-channel depth"
printf '\n==================================================\n[STEP 1/3] Generate finalized bifurcation CSV\n==================================================\n\n'
if [ "$CHECK_MAP" = check_map ]; then
    "$PYTHON_CMD" "$EXEC_SETPARAM" "$RIVHGT" "$BIFPRM_CSV" "$BIFLAYER" "$DIMINFO" check_map --map-format "$MAP_FORMAT"
else
    "$PYTHON_CMD" "$EXEC_SETPARAM" "$RIVHGT" "$BIFPRM_CSV" "$BIFLAYER" "$DIMINFO" --map-format "$MAP_FORMAT"
fi
printf '[SUCCESS] Generated %s\n' "$BIFPRM_CSV"

# 2. Convert the finalized CSV without reordering or recalculating its rows.
STEP="Convert finalized bifurcation CSV to NetCDF"
printf '\n==================================================\n[STEP 2/3] Convert CSV to NetCDF\n==================================================\n\n'
"$PYTHON_CMD" "$EXEC_CONVERT" "$BIFPRM_CSV" "$BIFPRM_NC"
printf '[SUCCESS] Generated %s from %s\n' "$BIFPRM_NC" "$BIFPRM_CSV"

# 3. Merge basins connected by the retained bifurcation pathways.
cd "$SCRIPT_DIR"

STEP="Merge basins connected by bifurcation pathways"
printf '\n==================================================\n[STEP 3/3] Merge connected basins\n==================================================\n\n'
if [ "$CHECK_MAP" = check_map ]; then
    "$PYTHON_CMD" "$EXEC_SETBASIN" check_map --map-format "$MAP_FORMAT"
else
    "$PYTHON_CMD" "$EXEC_SETBASIN" --map-format "$MAP_FORMAT"
fi
printf '[SUCCESS] Generated basin-connectivity products\n'

printf '\n==================================================\n[SUCCESS] %s\n==================================================\n' "$SCRIPT_NAME"
