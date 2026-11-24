#!/usr/bin/env bash
set -euo pipefail

# Internal path anchors; user paths below are independent of the caller's directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
TUTORIAL_DIR="$(CDPATH= cd "$SCRIPT_DIR/.." && pwd -P)"
REPO_ROOT="$(cd "$TUTORIAL_DIR/../.." && pwd -P)"

# User settings
# ----------------------------------------------------------------------
PYTHON_CMD="python3"                                                  # Python with NumPy, Matplotlib, rasterio and netCDF4.
MAP_DIR="map/glb_15min"                                               # Map path relative to repository root, or absolute.
TILE_CACHE="$HOME/.cache/cmf_flood_osm_tiles"                         # Existing OSM cache directory.
SETTINGS="$TUTORIAL_DIR/metadata/event_figure_settings.json"            # Authoritative panel_step1 display settings: extent, colors, dimensions/DPI, labels.
ZOOMUP_FILE="$TUTORIAL_DIR/metadata/event_map_extents.csv"              # Authoritative named viewing extents [degrees, CSV schema].
IMPACT_FILE="$TUTORIAL_DIR/metadata/01_impact_locations.csv"            # Reported locality metadata; not observed flood polygons.
OUTPUT="$TUTORIAL_DIR/figure/f01-reported_flood_impacts.png"            # Output PNG path.
SHOW_OSM=1                                                            # 1: use OSM backdrop; 0: omit tile requests.
SETTINGS_SECTION="panel_step1"                                        # Section key in SETTINGS; data/settings are not duplicated here.

# ----------------------------------------------------------------------
# User settings end here.
# ----------------------------------------------------------------------

# The guarded array expansion below also supports an empty list under Bash 3.2 with set -u.
EXTRA_ARGS=()
if [[ "$SHOW_OSM" == "0" ]]; then EXTRA_ARGS+=(--no-osm); fi
cd "$REPO_ROOT"
"$PYTHON_CMD" visualization/river_map/script/f06b-OSM_background-local_info.py \
    --map-dir "$MAP_DIR" --settings "$SETTINGS" --settings-section "$SETTINGS_SECTION" \
    --zoomup-file "$ZOOMUP_FILE" --plot-file "$IMPACT_FILE" \
    --tile-cache "$TILE_CACHE" --output "$OUTPUT" ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}
