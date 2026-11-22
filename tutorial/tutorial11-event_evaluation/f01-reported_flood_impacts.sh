#!/usr/bin/env bash
set -euo pipefail

# User settings
PYTHON_CMD="python3"
MAP_DIR="map/glb_15min"
TILE_CACHE="$HOME/.cache/cmf_flood_osm_tiles"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SETTINGS="$SCRIPT_DIR/metadata/event_figure_settings.json"
ZOOMUP_FILE="$SCRIPT_DIR/metadata/event_map_extents.csv"
IMPACT_FILE="$SCRIPT_DIR/impact_locations.csv"
FIGURE_DIR="$SCRIPT_DIR/figure"
cd "$REPO_ROOT"

"$PYTHON_CMD" visualization/river_map/script/f06b-OSM_background-local_info.py \
    --map-dir "$MAP_DIR" --settings "$SETTINGS" --settings-section panel_step1 \
    --zoomup-file "$ZOOMUP_FILE" --plot-file "$IMPACT_FILE" \
    --tile-cache "$TILE_CACHE" --output "$FIGURE_DIR/f01-reported_flood_impacts.png"

printf '\n[ SUCCESS ] Tutorial 11 Figure 1 written to %s\n' \
    "$FIGURE_DIR/f01-reported_flood_impacts.png"
