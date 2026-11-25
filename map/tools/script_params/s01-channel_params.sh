#!/bin/sh
# Generate annual-runoff channel parameters for a map.
# Copy to <map>/script_params/, configure the paths and coefficients, and run from any CWD.
#
# Inputs: diminfo_<ROFFTAG>.txt, inpmat_<ROFFTAG>.nc, annual runoff climatology,
#         nextxy.nc, ctmare.nc, and width.nc.
# Outputs: outclm.nc, rivwth.nc, rivhgt.nc, rivman.nc, rivhgt_inf.nc,
#          and rivwth_merit.nc in the map root.
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

# Runoff format, interpolation, and paired runoff-grid matrix files.
TYPE="bin"                                     # Runoff format: bin for binary or cdf for NetCDF.
INTERP="mat"                                   # Python CLI: mat for input matrix or near for nearest-grid.
# test-1deg: global ELSE_GPCC 360 x 180 grid; matrix is specific to this model map.
# Shared grid: inp/ELSE_GPCC/runoffYYYY.nc [mm/day] and map/data/ELSE_GPCC_clm-1981-2010.one [mm/s].
ROFFTAG="test-1deg"                        # Runoff dataset ID used in both matrix filenames.
DIMINFO="diminfo_${ROFFTAG}.txt"                 # Simulation dimension information (model and input grids).
INPMAT="inpmat_${ROFFTAG}.nc"                  # Runoff input matrix file derived from ROFFTAG.
CROFBIN="../data/ELSE_GPCC_clm-1981-2010.one"  # Annual-mean runoff input [mm/s], relative to the map root.
# Source: Kim et al. (2009), https://doi.org/10.1029/2009GL039006

# Channel cross-sections use H=max(HMIN,HC*Q**HP+HO) and W=max(WMIN,WC*Q**WP+WO), in m.
HC=0.1    # Depth coefficient [m/(m3/s)^HP].
HP=0.50   # Depth power-law exponent (dimensionless).
HO=0.00   # Depth offset [m].
HMIN=1.0  # Minimum channel depth [m].
WC=2.50   # Width coefficient [m/(m3/s)^WP].
WP=0.60   # Width power-law exponent (dimensionless).
WO=0.00   # Width offset [m].
WMIN=5.0  # Minimum channel width [m].

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------

# ${0##*/} removes the directory portion of the script path for readable messages.
SCRIPT_NAME=${0##*/}
STEP="Prepare channel-parameter workflow"
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
EXEC_OUTCLM="$CODE_DIR/param_channel_calc_outclm.py"
EXEC_RIVWTH="$CODE_DIR/param_channel_calc_rivwth.py"
EXEC_MERIT="$CODE_DIR/param_channel_set_merit_width.py"

cd "$MAP_DIR"

STEP="Calculate mean river discharge from annual runoff and the input matrix"
printf '\n==================================================\n[STEP 1/3] Calculate mean river discharge\n==================================================\n\n'
"$PYTHON_CMD" "$EXEC_OUTCLM" "$TYPE" "$INTERP" "$DIMINFO" "$CROFBIN"

# 2. Estimate width, depth, roughness, and the no-floodplain depth field.
STEP="Estimate channel width, depth, and roughness"
printf '\n==================================================\n[STEP 2/3] Estimate channel parameters\n==================================================\n\n'
"$PYTHON_CMD" "$EXEC_RIVWTH" "$TYPE" "$DIMINFO" "$HC" "$HP" "$HO" "$HMIN" \
    "$WC" "$WP" "$WO" "$WMIN"

# 3. Merge MERIT Hydro width estimates with the power-law river widths.
STEP="Merge power-law channel widths with MERIT Hydro widths"
printf '\n==================================================\n[STEP 3/3] Merge MERIT Hydro channel widths\n==================================================\n\n'
"$PYTHON_CMD" "$EXEC_MERIT" "$DIMINFO"

printf '\n==================================================\n[SUCCESS] %s\n==================================================\n' "$SCRIPT_NAME"
