#!/usr/bin/env bash
# Draw native-grid and 1-minute Python-downscaled flood depth for 2001-09-01.
set -euo pipefail
export MPLBACKEND=Agg

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VISUALIZATION_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$VISUALIZATION_DIR/.." && pwd)"

# User settings: snapshot, map extent, and shared flood-depth color scale.
TARGET_DATE="2001-09-01"
WEST=102
EAST=108
SOUTH=9
NORTH=15
DEPTH_MIN=0
DEPTH_MAX=20
DEPTH_TICKS="0,2,5,10,15,20"
COLORMAP="YlGnBu"

# User settings: output size and typography, reviewed on the combined Figure.
FIGURE_WIDTH=8.2
FIGURE_HEIGHT=9.0
DPI=200
TITLE_SIZE=14
AXIS_LABEL_SIZE=11
TICK_LABEL_SIZE=9
COLORBAR_LABEL_SIZE=11
PYTHON="$REPO_ROOT/.venv/bin/python" # Activate .venv before running this script.

SAMPLE_DIR="$SCRIPT_DIR/out_sample"
FIGURE_DIR="$SCRIPT_DIR/figure"
MAP_DIR="$REPO_ROOT/map/mekong_15min"
MAP1_DIR="$MAP_DIR/1min"
PARAMS_FILE="$MAP_DIR/params.txt"
LOCATION_FILE="$MAP1_DIR/location.txt"
SOURCE_NC="$SAMPLE_DIR/flddph_${TARGET_DATE}.nc"
DOWNSCALED_NC="$SAMPLE_DIR/flddph_1min_${TARGET_DATE}.nc"
PANEL_A="$FIGURE_DIR/f04a-flood_depth-raster.png"
PANEL_B="$FIGURE_DIR/f04b-flood_depth-downscale_1min.png"
FIGURE_FILE="$FIGURE_DIR/f04-flood_depth.png"
PLOTTER="$SCRIPT_DIR/script/f04-flood_depth.py"
DOWNSCALER="$REPO_ROOT/tools/output_analysis/downscale_flddph/script/downscale_flddph.py"
COMBINER="$VISUALIZATION_DIR/script/combine_panels.py"

printf '\n[STEP 1/3] Run the standalone Python downscaler.\n'
"$PYTHON" "$DOWNSCALER" --input "$SOURCE_NC" --map-dir "$MAP_DIR" --resolution 1min \
    --west "$WEST" --east "$EAST" --south "$SOUTH" --north "$NORTH" --output "$DOWNSCALED_NC"

printf '\n[STEP 2/3] Render both panels with the established visualization.\n'
"$PYTHON" "$PLOTTER" plot --source "$SOURCE_NC" --date "$TARGET_DATE" \
    --downscaled-netcdf "$DOWNSCALED_NC" \
    --flddif "$MAP1_DIR/1min.flddif.bin" --elevtn "$MAP1_DIR/1min.elevtn.bin" \
    --location "$LOCATION_FILE" --params "$PARAMS_FILE" \
    --panel-a "$PANEL_A" --panel-b "$PANEL_B" \
    --west "$WEST" --east "$EAST" --south "$SOUTH" --north "$NORTH" \
    --depth-min "$DEPTH_MIN" --depth-max "$DEPTH_MAX" --depth-ticks "$DEPTH_TICKS" \
    --cmap "$COLORMAP" --title-size "$TITLE_SIZE" --axis-label-size "$AXIS_LABEL_SIZE" \
    --tick-label-size "$TICK_LABEL_SIZE" --colorbar-label-size "$COLORBAR_LABEL_SIZE" \
    --figure-width "$FIGURE_WIDTH" --figure-height "$FIGURE_HEIGHT" --dpi "$DPI"

printf '\n[STEP 3/3] Assemble the two map panels side by side.\n'
"$PYTHON" "$COMBINER" "$PANEL_A" "$PANEL_B" --output "$FIGURE_FILE" \
    --layout grid --columns 2 --align-map-areas --gap 20 --margin 20 --dpi "$DPI"

printf '\n[SUCCESS] Created p02-f04 Flood Depth with the Python package.\n'
printf 'Downscaled sample: %s\n' "$DOWNSCALED_NC"
printf 'Combined figure: %s\n' "$FIGURE_FILE"
