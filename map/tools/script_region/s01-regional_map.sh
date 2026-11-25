#!/bin/sh
# Prepare a regional map from a source map using the bounds below.
# Copy to the target map and run from that map's script_region/ directory.
set -eu

# CaMa-Flood general setting (check CMF root, import shell error checker)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/code/cmf_check_shell_error.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
SOURCE="../../glb_15min/"  # Source map relative to this script_region/ directory; keep trailing slash.
WEST="90.0"                # Western boundary (degrees longitude).
EAST="110.0"               # Eastern boundary (degrees longitude).
SOUTH="5.0"                # Southern boundary (degrees latitude).
NORTH="35.0"               # Northern boundary (degrees latitude).

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
cmf_check_init "Regional map preparation"

cmf_check_step 1 6 "Save source-map path and requested geographic bounds"
printf '%s\n' "$SOURCE" "$WEST" "$EAST" "$SOUTH" "$NORTH" > region_info.txt

cmf_check_step 2 6 "Crop the source map to the requested region"
"$PYTHON_CMD" "$CODE_DIR/region_cut_domain.py"

cmf_check_step 3 6 "Retain bifurcation pathways inside the regional domain"
"$PYTHON_CMD" "$CODE_DIR/region_cut_bifway.py"

cmf_check_step 4 6 "Derive regional river and basin maps"
"$PYTHON_CMD" "$CODE_DIR/region_set_map.py"

# Process each supported high-resolution source when its location metadata exists.
for HIRES in 1min 30sec 15sec 5sec 3sec 1sec; do
    if [ -f "$SOURCE/$HIRES/location.txt" ]; then
        cmf_check_step 5 6 "Crop the $HIRES high-resolution data"
        mkdir -p "../$HIRES"
        "$PYTHON_CMD" "$CODE_DIR/region_combine_hires.py" "$HIRES"
    fi
done

# Create the standard climatology matrix from the first available resolution.
INPMAT_HIRES=""
for HIRES in 1min 30sec 15sec 5sec 3sec 1sec; do
    if [ -f "../$HIRES/location.txt" ]; then
        INPMAT_HIRES=$HIRES
        break
    fi
done
if [ -n "$INPMAT_HIRES" ]; then
    cmf_check_step 6 6 "Build the standard runoff-climatology matrix from $INPMAT_HIRES data"
    "$PYTHON_CMD" "$CODE_DIR/region_default_inpmat.py" "$INPMAT_HIRES"
fi

cmf_check_success
