#!/bin/sh
# Generate bifurcation CSV/NetCDF parameters and standard basin connectivity.
# Copy to <map>/script_params/, configure settings, and run from any CWD.
#
# Inputs: params.txt, nextxy.nc, basin.nc, bifori.txt, rivhgt.nc,
#         and diminfo_<ROFFTAG>.txt in the map root.
# Outputs: bifprm.csv, bifprm.nc, bifbsn.nc, bifcol.nc; optional check maps.
set -eu

: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/code/cmf_check_shell_error.sh"

# User settings
PYTHON_CMD="python3"
BIFLAYER=5                      # Number of bifori.txt layers to process (1-10).
# test-1deg: global ELSE_GPCC 360 x 180 grid; matrix is specific to this model map.
# Use the same grid tag as s01, which reads map/data/ELSE_GPCC_clm-1981-2010.nc.
ROFFTAG="test-1deg"         # Runoff dataset ID used to derive DIMINFO.
DIMINFO="diminfo_${ROFFTAG}.txt"  # Simulation dimension information (model and input grids).
RIVHGT="rivhgt.nc"              # Channel-depth map used to estimate bifurcation depth.
BIFPRM_CSV="bifprm.csv"         # Finalized, named bifurcation parameter table.
BIFPRM_NC="bifprm.nc"           # NetCDF conversion at the map root.
# Optional diagnostic maps (uncomment the second line to enable).
CHECK_MAP=""
#CHECK_MAP="--check-map"

# Legacy map format; change only when using a legacy Binary map.
MAP_FORMAT="netcdf"

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
MAP_DIR=$(CDPATH= cd "$SCRIPT_DIR/.." && pwd -P)
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
cmf_check_init "Bifurcation parameter calculation"

cd "$MAP_DIR"

cmf_check_step 1 3 "Generate finalized bifurcation CSV"
"$PYTHON_CMD" "$CODE_DIR/param_bif_set_params.py" \
    "$RIVHGT" "$BIFPRM_CSV" "$BIFLAYER" "$DIMINFO" \
    ${CHECK_MAP:+"$CHECK_MAP"} --map-format "$MAP_FORMAT"

cmf_check_step 2 3 "Convert finalized bifurcation CSV to NetCDF"
"$PYTHON_CMD" "$CODE_DIR/convert_bifprm_csv_to_netcdf.py" "$BIFPRM_CSV" "$BIFPRM_NC"

cd "$SCRIPT_DIR"

cmf_check_step 3 3 "Merge basins connected by bifurcation pathways"
"$PYTHON_CMD" "$CODE_DIR/param_bif_set_basin.py" \
    ${CHECK_MAP:+"$CHECK_MAP"} --map-format "$MAP_FORMAT"

cmf_check_success
