#!/bin/sh
# Estimate annual-runoff channel parameters for this map.
# Run from this map's script_params/ directory.
# Inputs: paired diminfo/inpmat files, runoff climatology, and map channel data.
# Outputs: channel parameter maps in the map root.
set -eu

# CaMa-Flood general setting (check CMF root, import shell error checker)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/code/cmf_check_shell_error.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
ROFFTAG="test-1deg"                         # Runoff grid identifier in the paired matrix filenames.
DIMINFO="../diminfo_${ROFFTAG}.txt"         # Simulation and runoff grid dimensions.
CROFNC="$CMF_V50_ROOT/map/data/ELSE_GPCC_clm-1981-2010.nc"  # Annual-mean runoff [mm/s].
# Source: Kim et al. (2009), https://doi.org/10.1029/2009GL039006

# H=max(HMIN,HC*Q**HP+HO), W=max(WMIN,WC*Q**WP+WO); channel dimensions are metres.
HC=0.1    # Depth coefficient [m/(m3/s)^HP].
HP=0.50   # Depth power-law exponent.
HO=0.00   # Depth offset [m].
HMIN=1.0  # Minimum channel depth [m].
WC=2.50   # Width coefficient [m/(m3/s)^WP].
WP=0.60   # Width power-law exponent.
WO=0.00   # Width offset [m].
WMIN=5.0  # Minimum channel width [m].

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
cmf_check_init "Channel parameter calculation"

cmf_check_step 1 3 "Calculate mean river discharge from runoff and the input matrix"
"$PYTHON_CMD" "$CODE_DIR/param_channel_calc_outclm.py" "$DIMINFO" "$CROFNC" --map-dir ..

cmf_check_step 2 3 "Estimate channel width, depth, and roughness"
"$PYTHON_CMD" "$CODE_DIR/param_channel_calc_rivwth.py" "$DIMINFO" \
    "$HC" "$HP" "$HO" "$HMIN" "$WC" "$WP" "$WO" "$WMIN" --map-dir ..

cmf_check_step 3 3 "Merge power-law widths with MERIT Hydro widths"
"$PYTHON_CMD" "$CODE_DIR/param_channel_set_merit_width.py" "$DIMINFO" --map-dir ..

cmf_check_success

# ----------------------------------------------------------------------
# Optional Python CLI flags (add directly to the matching command above)
# param_channel_calc_outclm.py: --runoff-binary, --interp-near, --map-format binary
# param_channel_calc_rivwth.py: --no-rivpar-netcdf, --map-format binary
# param_channel_set_merit_width.py: --map-format binary
# See each program's --help for details.
# ----------------------------------------------------------------------
