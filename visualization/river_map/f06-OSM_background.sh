#!/usr/bin/env bash
# User settings for Gallery method p01-f06 OSM_background.
# Panel a gives basin context and the f06b zoom box; panel b plots reported impact localities.
PYTHON_CMD="python3"
MAP_DIR="map/glb_15min"
WEST=3
SOUTH=46
EAST=12
NORTH=53
TARGET_BASIN=74
OUTPUT_A="visualization/river_map/figure/f06a-OSM_background.png"
OUTPUT_B="visualization/river_map/figure/f06b-impact_localities.png"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"
"$PYTHON_CMD" visualization/river_map/script/f06-OSM_background.py \
    --panel a --map-dir "$MAP_DIR" --west "$WEST" --south "$SOUTH" \
    --east "$EAST" --north "$NORTH" --target-basin "$TARGET_BASIN" --output "$OUTPUT_A"
"$PYTHON_CMD" visualization/river_map/script/f06-OSM_background.py \
    --panel b --map-dir "$MAP_DIR" --output "$OUTPUT_B"
