#!/bin/sh
# Generate bifurcation parameters and basin-connectivity maps.
# Run from this map's script_params/ directory after channel parameters exist.
# Inputs: ../params.nml, ../nextxy.nc, ../basin.nc, ../bifori.csv, ../rivhgt.nc.
# Outputs: bifprm.csv, bifprm.nc, bifbsn.nc, bifcol.nc in the map root.
set -eu

# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
BIFLAYER=5                       # Total width fields including channel width (1-10).
ROFFTAG="test-1deg"             # Must match the runoff grid used for the paired diminfo file.
DIMINFO="../diminfo_${ROFFTAG}.nml"
RIVHGT="../rivhgt.nc"           # Channel-depth map for bifurcation-depth estimates.
BIFPRM_CSV="../bifprm.csv"      # Finalized source-order table.
BIFPRM_NC="../bifprm.nc"        # NetCDF copy of the finalized table.

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"

cmf_check_init "Bifurcation parameter calculation"

cmf_check_step 1 3 "Generate the finalized bifurcation CSV"
"$PYTHON_CMD" "$CODE_DIR/param_bif_set_params.py" \
    "$RIVHGT" "$BIFPRM_CSV" "$BIFLAYER" "$DIMINFO" --map-dir ..

cmf_check_step 2 3 "Convert the finalized bifurcation CSV to NetCDF"
"$PYTHON_CMD" "$CODE_DIR/convert_bifprm_csv_to_netcdf.py" "$BIFPRM_CSV" "$BIFPRM_NC"

cmf_check_step 3 3 "Merge basins linked by bifurcation pathways"
"$PYTHON_CMD" "$CODE_DIR/param_bif_set_basin.py" --map-dir ..

cmf_check_success

# ----------------------------------------------------------------------
# Optional Python CLI flags (add directly to the matching command above)
# param_bif_set_params.py / param_bif_set_basin.py: --check-map, --map-format binary
# Add --check-map to both commands above to write inspection-only maps.
# ----------------------------------------------------------------------
