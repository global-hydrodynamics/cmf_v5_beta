#!/usr/bin/env bash
set -euo pipefail

# Internal path anchors; user paths below are independent of the caller's directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
TUTORIAL_DIR="$SCRIPT_DIR"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"

# User settings
# ----------------------------------------------------------------------
PYTHON_CMD="python3"                                                  # Python with plotting and catalogue dependencies.
DOMAIN_CONFIG="$TUTORIAL_DIR/metadata/02_domain_selection.json"       # Authoritative search dates, analysis bbox and view extent.
ATLANTIS_DIR="$TUTORIAL_DIR/Atlantis"                                 # Existing catalogue and log root.
MAP_DIR="$REPO_ROOT/map/glb_15min"                                    # River-map context path.
TILE_CACHE="$HOME/.cache/cmf_flood_osm_tiles"                         # OSM cache directory.
FIGURE_DIR="$TUTORIAL_DIR/figure"                                     # Output PNG directory; one page per six passes.
FIG_WIDTH=15                                                          # Canvas width [inches].
FIG_HEIGHT=10                                                         # Positive canvas height [inches].
DPI=180                                                               # PNG resolution [pixels/inch].
SHOW_OSM=1                                                            # 1: OSM context; 0: no tile requests.

# ----------------------------------------------------------------------
# User settings end here.
# ----------------------------------------------------------------------

if [[ ! -s "$TUTORIAL_DIR/metadata/03a_satellite_pass_inventory.csv" || \
      ! -s "$TUTORIAL_DIR/metadata/03a_satellite_orbit_metadata.csv" || \
      ! -s "$TUTORIAL_DIR/metadata/03a_sentinel1_acquisition_footprints.geojson" ]]; then
    printf 'Step 3a metadata is missing. Run bash s03a-satellite_availability.sh first.\n' >&2
    exit 1
fi

export MPLCONFIGDIR="$ATLANTIS_DIR/logs/matplotlib"
# The guarded array expansion below also supports an empty list under Bash 3.2 with set -u.
EXTRA_ARGS=()
if [[ "$SHOW_OSM" == "0" ]]; then EXTRA_ARGS+=(--no-osm); fi
"$PYTHON_CMD" "$TUTORIAL_DIR/script/s03a-gfm_availability.py"  \
    --mode figure \
    --domain-config "$DOMAIN_CONFIG" \
    --catalogue-root "$ATLANTIS_DIR/catalogue"  \
    --inventory-output "$TUTORIAL_DIR/metadata/03a_satellite_pass_inventory.csv"  \
    --orbit-metadata "$TUTORIAL_DIR/metadata/03a_satellite_orbit_metadata.csv"  \
    --acquisition-footprints "$TUTORIAL_DIR/metadata/03a_sentinel1_acquisition_footprints.geojson"  \
    --map-dir "$MAP_DIR" \
    --tile-cache "$TILE_CACHE" \
    --figure-dir "$FIGURE_DIR"  \
    --fig-width "$FIG_WIDTH" \
    --fig-height "$FIG_HEIGHT" \
    --dpi "$DPI" ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}
