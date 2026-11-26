#!/bin/sh
set -eu

# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
# Editable examples, not universal scientific parameters.
AREA_THRESHOLD1_KM2=30000
AREA_THRESHOLD2_KM2=5000  # Set empty for the single-stage segmentation.
# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"

cmf_check_init "Generate sample subbasin segmentation"

if [ -n "$AREA_THRESHOLD2_KM2" ]; then

    cmf_check_step 1 1 "Segment the river network at the ${AREA_THRESHOLD1_KM2}/${AREA_THRESHOLD2_KM2} km2 thresholds"
    "$PYTHON_CMD" "$CODE_DIR/analysis_subbasin.py" "$AREA_THRESHOLD1_KM2" \
        "$AREA_THRESHOLD2_KM2" ../subbsn-sample.bin ../subcol-sample.bin --map-dir ..
else

    cmf_check_step 1 1 "Segment the river network at the ${AREA_THRESHOLD1_KM2} km2 threshold"
    "$PYTHON_CMD" "$CODE_DIR/analysis_subbasin.py" "$AREA_THRESHOLD1_KM2" \
        ../subbsn-sample.bin ../subcol-sample.bin --map-dir ..
fi

cmf_check_success

# Optional Python CLI flags: add --map-format binary to use legacy Binary maps.
