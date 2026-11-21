#!/usr/bin/env bash
set -euo pipefail

# User settings
PYTHON_CMD="python3"
MAP_DIR="map/glb_15min"
SETTINGS="visualization/river_map/data/f06_settings.json"
ZOOMUP_FILE="visualization/river_map/data/f06b_zoomup.csv"
PLOT_FILE="visualization/river_map/data/f06b_plot.csv"
FIGURE_DIR="visualization/river_map/figure"
TILE_CACHE="${HOME}/.cache/cmf_flood_osm_tiles"
GAP=24
MARGIN=24
DPI=180

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VISUALIZATION_DIR="$REPO_ROOT/visualization"
cd "$REPO_ROOT"

PANEL_A="$FIGURE_DIR/f06a-OSM_background-default.png"
PANEL_B="$FIGURE_DIR/f06b-OSM_background-local_info.png"
OUTPUT_FILE="$FIGURE_DIR/f06-OSM_background.png"

printf '\n[STEP 1/3] Draw f06a basin overview: OSM_background-default.\n'
"$PYTHON_CMD" visualization/river_map/script/f06a-OSM_background-default.py \
    --map-dir "$MAP_DIR" --settings "$SETTINGS" --zoomup-file "$ZOOMUP_FILE" \
    --tile-cache "$TILE_CACHE" --output "$PANEL_A"

printf '\n[STEP 2/3] Draw f06b local event information: OSM_background-local_info.\n'
"$PYTHON_CMD" visualization/river_map/script/f06b-OSM_background-local_info.py \
    --map-dir "$MAP_DIR" --settings "$SETTINGS" --zoomup-file "$ZOOMUP_FILE" \
    --plot-file "$PLOT_FILE" --tile-cache "$TILE_CACHE" --output "$PANEL_B"

printf '\n[STEP 3/3] Combine f06a and f06b into OSM_background.\n'
"$PYTHON_CMD" "$VISUALIZATION_DIR/script/combine_panels.py" \
    "$PANEL_A" "$PANEL_B" --layout horizontal --gap "$GAP" --margin "$MARGIN" \
    --dpi "$DPI" --output "$OUTPUT_FILE"

printf '\n[SUCCESS] Created the f06 figure: %s\n' "$OUTPUT_FILE"
