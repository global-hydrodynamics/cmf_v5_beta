#!/bin/sh
set -eu

# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
GRDC_ALLOC="../GRDC_alloc.txt"  # Allocation from t01-alloc_flow_gauge.sh or a supplied table.
# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
cd "$SCRIPT_DIR"

printf '%s\n' "Example: Select a GRDC station allocated to this map, then calculate its upstream basin."
printf '%s\n' "Different map grids can assign the same location to different cells; use the map-specific allocation instead of fixed coordinates."
if [ ! -f "$GRDC_ALLOC" ]; then
    printf 'GRDC allocation not found: %s. Run t01-alloc_flow_gauge.sh or provide the table.\n' "$GRDC_ALLOC" >&2
    exit 1
fi

# Preserve the established selection: valid type, positive mapped area and primary indices;
# the first row wins if multiple stations share the maximum area_CaMa.
if ! SELECTED=$(awk 'NR > 1 && $8 != -9 && $9 > 0 && $10 > 0 && $5 > max {max=$5; id=$1; ix=$9; iy=$10} END {if (id == "") exit 1; print id, ix, iy, max}' "$GRDC_ALLOC"); then
    printf 'GRDC allocation contains no valid allocated station: %s\n' "$GRDC_ALLOC" >&2
    exit 1
fi
set -- $SELECTED
GRDC_ID=$1
IX=$2
IY=$3
AREA_CAMA=$4
printf 'Selected GRDC station: %s\nGrid cell (1-based, Fortran): IX=%s, IY=%s\nCaMa-Flood upstream area: %s km2\n' \
    "$GRDC_ID" "$IX" "$IY" "$AREA_CAMA"
printf 'ID\tix1\tiy1\tarea_CaMa_km2\n%s\t%s\t%s\t%s\n' \
    "$GRDC_ID" "$IX" "$IY" "$AREA_CAMA" > ../grdc_station_selection.txt

printf '%s\n' 'Inspecting the selected river cell:'
./get_river_point_info.sh xy "$IX" "$IY" | tee ../grdc_river_info.txt
./calc_upbasin.sh xy "$IX" "$IY" "../upbasin-${GRDC_ID}.nc"
