#!/bin/sh
set -eu

# CaMa-Flood general setting (check CMF root, import shell error checker)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
GAUGE_IN="../../data/GRDC_allocated.csv"  # MERIT Hydro-preallocated GRDC station table.
GAUGE_MODE="multi"                     # Allocation mode: multi or single.
HIRES_TAG=""                            # Empty selects the coarsest installed NetCDF resolution.
# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
cmf_check_init "Allocate GRDC flow gauges to CaMa-Flood catchments"
if [ -z "$HIRES_TAG" ]; then
    for tag in 1min 30sec 15sec 5sec 3sec 1sec; do
        if [ -d "../$tag" ]; then HIRES_TAG=$tag; break; fi
    done
fi
[ -n "$HIRES_TAG" ] || { printf 'No high-resolution map directory found in the map root.\n' >&2; exit 1; }
cmf_check_step 1 1 "Allocate GRDC gauges using the $HIRES_TAG map"
"$PYTHON_CMD" "$CODE_DIR/allocate_flow_gauge.py" "$GAUGE_IN" "$GAUGE_MODE" \
    "$HIRES_TAG" --map-dir .. --output-dir ..

cmf_check_success

# Optional Python CLI flag: add --map-format binary for a legacy Binary map.
