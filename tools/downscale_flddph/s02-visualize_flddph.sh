#!/usr/bin/env bash
set -eu

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

# User settings: input fields, map context, plot extent and display scale.
PYTHON="python3"
MAPDIR="${PACKAGE_DIR}/../../map/mekong_15min"
INPUT_NC="${PACKAGE_DIR}/sample_mekong/out/flddph_2001-09-01.nc"
DOWNSCALED_NC="${PACKAGE_DIR}/sample_mekong/downscaled/flddph_1min_2001-09-01.nc"
FIGURE="${PACKAGE_DIR}/sample_mekong/figure/flood_depth_2001-09-01.png"
WEST=102.0
EAST=108.0
SOUTH=9.0
NORTH=15.0
RES="1min"
DEPTH_MIN=0.0
DEPTH_MAX=20.0
FIGURE_WIDTH=12.0
FIGURE_HEIGHT=5.8
DPI=180

# User settings end here.

"$PYTHON" "$PACKAGE_DIR/script/visualize_flddph.py" \
    --input "$INPUT_NC" --downscaled "$DOWNSCALED_NC" --map-dir "$MAPDIR" \
    --resolution "$RES" --output "$FIGURE" \
    --west "$WEST" --east "$EAST" --south "$SOUTH" --north "$NORTH" \
    --depth-min "$DEPTH_MIN" --depth-max "$DEPTH_MAX" \
    --figure-width "$FIGURE_WIDTH" --figure-height "$FIGURE_HEIGHT" --dpi "$DPI"

printf '[SUCCESS] Created flood-depth Figure: %s\n' "$FIGURE"
