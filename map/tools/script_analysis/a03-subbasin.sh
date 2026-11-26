#!/bin/sh
set -eu

# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
AREA_SUBBSN=30000   # Primary drainage-area subdivide threshold [km2].
AREA_SMLBSN=5000    # Secondary threshold [km2]; empty to disable stage 2 (put ID to smaller basin).
#AREA_SMLBSN=""       # in case small basin threshold is not used.

TAG="-sample"  # Output filename suffix; empty for subbsn.nc and subcol.nc.
#TAG="-${AREA_SUBBSN}-${AREA_SMLBSN}"  # Include thresholds in filenames.
# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"

cmf_check_init "Generate subbasin segmentation"

cmf_check_step 1 1 "Segment river network (primary threshold: ${AREA_SUBBSN} km2)"
"$PYTHON_CMD" "$CODE_DIR/analysis_subbasin.py" \
    "$AREA_SUBBSN" ${AREA_SMLBSN:+"$AREA_SMLBSN"} \
    "../subbsn${TAG}.nc" "../subcol${TAG}.nc" --map-dir ..

cmf_check_success

# Optional Python CLI flags: add --map-format binary to use legacy Binary maps.
