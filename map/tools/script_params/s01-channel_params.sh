#!/bin/sh
# Generate annual-runoff channel parameters for a map.
# Copy to <map>/script_params/, configure the paths and coefficients, and run from any CWD.
#
# Inputs: diminfo_<ROFFTAG>.txt, inpmat_<ROFFTAG>.nc, annual runoff climatology,
#         nextxy.nc, ctmare.nc, and width.nc.
# Outputs: outclm.nc, rivwth.nc, rivhgt.nc, rivman.nc, rivhgt_inf.nc,
#          rivpar.nc, and rivwth_merit.nc in the map root.
set -eu

# CaMa-Flood general setting (check CMF root, import shell error checker)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/code/cmf_check_shell_error.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
ROFFTAG="test-1deg"                             # Runoff dataset ID used in paired matrix filenames.
DIMINFO="diminfo_${ROFFTAG}.txt"               # Simulation dimension information (model and input grids).
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

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
MAP_DIR=$(CDPATH= cd "$SCRIPT_DIR/.." && pwd -P)
CODE_DIR="$CMF_V50_ROOT/map/tools/code"

cmf_check_init "Channel parameter calculation"
cd "$MAP_DIR"

cmf_check_step 1 3 "Calculate mean river discharge from annual runoff and the input matrix"
"$PYTHON_CMD" "$CODE_DIR/param_channel_calc_outclm.py" \
    "$DIMINFO" "$CROFNC"

cmf_check_step 2 3 "Estimate channel width, depth, and roughness"
"$PYTHON_CMD" "$CODE_DIR/param_channel_calc_rivwth.py" \
    "$DIMINFO" "$HC" "$HP" "$HO" "$HMIN" \
    "$WC" "$WP" "$WO" "$WMIN"

cmf_check_step 3 3 "Merge power-law channel widths with MERIT Hydro widths"
"$PYTHON_CMD" "$CODE_DIR/param_channel_set_merit_width.py" \
    "$DIMINFO"

cmf_check_success

# ----------------------------------------------------------------------
# Optional Python CLI flags
# Add options directly to the corresponding Python command when needed.
#
# Step 1: param_channel_calc_outclm.py
#   --runoff-binary : Use legacy Binary runoff input.
#   --interp-near   : Use nearest-grid runoff interpolation.
#   --map-binary    : Use legacy Binary map I/O.
#
# Step 2: param_channel_calc_rivwth.py
#   --map-binary : Use legacy Binary map I/O.
#   --no-rivpar-netcdf : Skip the supplementary rivpar.nc output.
#
# Step 3: param_channel_set_merit_width.py
#   --map-binary : Use legacy Binary map I/O.
#
# See each Python program's --help for details.
# ----------------------------------------------------------------------
