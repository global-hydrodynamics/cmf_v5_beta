#!/usr/bin/env bash
set -eu

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

# User settings: existing Duration outputs, map context, and display extent.
PYTHON="python3"
TABLE_NC="${PACKAGE_DIR}/sample_mekong/out/flood_duration_table_2001.nc"
DURATION_NC="${PACKAGE_DIR}/sample_mekong/downscaled/flood_duration_1min_2001.nc"
MAPDIR="/path/to/map/mekong_15min"
RES="1min"
FIGURE="${PACKAGE_DIR}/sample_mekong/figure/flood_duration_2001.png"
WEST=102.0
EAST=108.0
SOUTH=9.0
NORTH=15.0
NATIVE_THRESHOLD=0.01
MAX_DAYS=365
FIGURE_WIDTH=12.0
FIGURE_HEIGHT=5.8
DPI=180

# User settings end here.

for input_path in "$TABLE_NC" "$DURATION_NC"; do
    if [[ ! -f "$input_path" ]]; then
        printf '[ERROR] Required input not found: %s\nRun t01-downscale_duration.sh first and set INPUT_FILE.\n' "$input_path" >&2
        exit 1
    fi
done

"$PYTHON" "$PACKAGE_DIR/script/visualize_duration.py" \
    --table "$TABLE_NC" --downscaled "$DURATION_NC" --map-dir "$MAPDIR" \
    --resolution "$RES" --output "$FIGURE" --west "$WEST" --east "$EAST" \
    --south "$SOUTH" --north "$NORTH" --native-threshold "$NATIVE_THRESHOLD" \
    --max-days "$MAX_DAYS" --figure-width "$FIGURE_WIDTH" --figure-height "$FIGURE_HEIGHT" --dpi "$DPI"

printf '[SUCCESS] Created Duration Figure: %s\n' "$FIGURE"
