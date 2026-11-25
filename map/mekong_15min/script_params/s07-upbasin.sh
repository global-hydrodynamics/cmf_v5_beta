#!/bin/sh
set -eu

# CaMa-Flood general setting (check CMF root, import shell error checker)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
GRDC_ALLOC="../GRDC_alloc.txt"  # Create with t01-alloc_flow_gauge.sh or provide this table.
# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
cmf_check_init "Create an upstream-basin example from the largest valid GRDC station"

cmf_check_step 1 3 "Select the valid allocated station with the largest CaMa area"
SELECTED=$(awk 'NR > 1 && $8 != -9 && $9 > 0 && $10 > 0 && $5 > max {max=$5; id=$1; ix=$9; iy=$10} END {if (id == "") exit 1; print id, ix, iy, max}' "$GRDC_ALLOC")
set -- $SELECTED
GRDC_ID=$1
IX=$2
IY=$3
AREA_CAMA=$4
printf 'ID\tix1\tiy1\tarea_CaMa_km2\n%s\t%s\t%s\t%s\n' \
    "$GRDC_ID" "$IX" "$IY" "$AREA_CAMA" > ../grdc_station_selection.txt

cmf_check_step 2 3 "Inspect the selected GRDC river cell"
"$PYTHON_CMD" "$CODE_DIR/analysis_river_point_info.py" xy "$IX" "$IY" \
    --map-dir .. > ../grdc_river_info.txt

cmf_check_step 3 3 "Write the selected station's upstream-basin mask"
"$PYTHON_CMD" "$CODE_DIR/analysis_upbasin.py" "$IX" "$IY" \
    "../upbasin-${GRDC_ID}.bin" --map-dir ..
printf 'Selected GRDC station %s at cell (%s, %s), CaMa area %s km2.\n' "$GRDC_ID" "$IX" "$IY" "$AREA_CAMA"
cmf_check_success

# Optional Python CLI flags: add --map-format binary to use legacy Binary maps.
