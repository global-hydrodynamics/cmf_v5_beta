#!/usr/bin/env bash
# User settings for Gallery method p01-f06 OSM_background.
# Renders the existing CaMa vector river network over OSM Standard.
PYTHON_CMD="python3"
MAP_DIR="map/glb_15min"
WEST=3
SOUTH=46
EAST=12
NORTH=53
OUTPUT="visualization/gallery/p01-f06-OSM_background.png"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"
"$PYTHON_CMD" visualization/river_map/script/f06-OSM_background.py \
    --map-dir "$MAP_DIR" --west "$WEST" --south "$SOUTH" \
    --east "$EAST" --north "$NORTH" --output "$OUTPUT"
