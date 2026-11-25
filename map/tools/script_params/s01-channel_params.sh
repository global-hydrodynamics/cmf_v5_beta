#!/bin/sh
# Generate annual-runoff channel parameters for a map.
# Copy to <map>/script_params/, configure the paths and coefficients, and run from any CWD.
#
# Inputs: diminfo_<ROFFTAG>.txt, inpmat_<ROFFTAG>.nc, annual runoff climatology,
#         nextxy.nc, ctmare.nc, and width.nc.
# Outputs: outclm.nc, rivwth.nc, rivhgt.nc, rivman.nc, rivhgt_inf.nc,
#          and rivwth_merit.nc in the map root.
set -eu

: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/code/cmf_check_shell_error.sh"

# User settings
PYTHON_CMD="python3"

# Runoff format, interpolation, and paired runoff-grid matrix files.
TYPE="cdf"                                     # Runoff format: bin for binary or cdf for NetCDF.
INTERP="mat"                                   # Python CLI: mat for input matrix or near for nearest-grid.
# test-1deg: global ELSE_GPCC 360 x 180 grid; matrix is specific to this model map.
# Shared grid: inp/ELSE_GPCC/runoffYYYY.nc [mm/day] and map/data/ELSE_GPCC_clm-1981-2010.nc [mm/s].
ROFFTAG="test-1deg"                             # Runoff dataset ID used in both matrix filenames.
DIMINFO="diminfo_${ROFFTAG}.txt"               # Simulation dimension information (model and input grids).
INPMAT="inpmat_${ROFFTAG}.nc"                  # Runoff input matrix file derived from ROFFTAG.
CROFNC="$CMF_V50_ROOT/map/data/ELSE_GPCC_clm-1981-2010.nc"  # Annual-mean runoff input [mm/s].
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

# Legacy map format; change only when using a legacy Binary map.
MAP_FORMAT="netcdf"

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
MAP_DIR=$(CDPATH= cd "$SCRIPT_DIR/.." && pwd -P)

cmf_check_init "Channel parameter calculation"

CODE_DIR="$CMF_V50_ROOT/map/tools/code"
cd "$MAP_DIR"

cmf_check_step 1 3 "Calculate mean river discharge from annual runoff and the input matrix"
"$PYTHON_CMD" "$CODE_DIR/param_channel_calc_outclm.py" \
    "$TYPE" "$INTERP" "$DIMINFO" "$CROFNC" --map-format "$MAP_FORMAT"

cmf_check_step 2 3 "Estimate channel width, depth, and roughness"
"$PYTHON_CMD" "$CODE_DIR/param_channel_calc_rivwth.py" "$TYPE" "$DIMINFO" \
    "$HC" "$HP" "$HO" "$HMIN" \
    "$WC" "$WP" "$WO" "$WMIN" \
    --map-format "$MAP_FORMAT"

cmf_check_step 3 3 "Merge power-law channel widths with MERIT Hydro widths"
"$PYTHON_CMD" "$CODE_DIR/param_channel_set_merit_width.py" \
    "$DIMINFO" --map-format "$MAP_FORMAT"

cmf_check_success
