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
GAUGE_FILE="$SCRIPT_DIR/metadata/step2_gauges.csv"
FIGURE_DIR="$SCRIPT_DIR/figure"
cd "$REPO_ROOT"

"$PYTHON_CMD" visualization/river_map/script/f06a-OSM_background-default.py \
    --map-dir "$MAP_DIR" --settings "$SETTINGS" --zoomup-file "$ZOOMUP_FILE" \
    --plot-file "$IMPACT_FILE" --station-file "$GAUGE_FILE" \
    --tile-cache "$TILE_CACHE" \
    --output "$FIGURE_DIR/f02-simulation_observation_domain_design.png"

printf '\n[ SUCCESS ] Tutorial 11 Figure 2 written to %s\n' \
    "$FIGURE_DIR/f02-simulation_observation_domain_design.png"
