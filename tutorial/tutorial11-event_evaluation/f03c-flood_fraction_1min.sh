#!/usr/bin/env bash
set -euo pipefail

# Internal path anchors; user paths below are independent of the caller's directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
TUTORIAL_DIR="$SCRIPT_DIR"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"

# User settings
# ----------------------------------------------------------------------
PYTHON_CMD="${PYTHON_CMD:-python3}"                                   # Python executable; existing PYTHON_CMD override is supported.
INPUT="$TUTORIAL_DIR/observation/GFM_extent/GFM_S1A_20210715_o038784_dt049389_extent20m.tif" # Native categorical raster; classes 0–6, NoData 255.
DOMAIN_CONFIG="$TUTORIAL_DIR/metadata/02_domain_selection.json"       # Authoritative AOI [west,south,east,north degrees].
OUTPUT="$TUTORIAL_DIR/observation/GFM_extent/GFM_S1A_20210715_o038784_dt049389_floodfrac_1min.tif" # Derived 1min valid-support Flood Fraction [%].
COVERAGE_OUTPUT="$TUTORIAL_DIR/Atlantis/analysis/GFM_S1A_20210715_o038784_dt049389_valid_pixel_count_1min.tif" # Valid source-pixel counts; not physical area.
FOCUS_AREAS="$TUTORIAL_DIR/metadata/03c_focus_areas.json"             # Authoritative focus bboxes and IDs; selection not duplicated in Shell.
IMPACT_LOCATIONS="$TUTORIAL_DIR/metadata/01_impact_locations.csv"     # Context locality markers; not flood-selection criteria.
FIGURE_OUTPUT="$TUTORIAL_DIR/figure/f03c-gfm_flood_fraction_1min.png" # Output PNG path.
MAP_DIR="$REPO_ROOT/map/glb_15min"                                    # Context river-map path.
TILE_CACHE="$HOME/.cache/cmf_flood_osm_tiles"                         # OSM cache directory.
FIG_WIDTH=12.5                                                        # Canvas width [inches].
FIG_HEIGHT=8.2                                                        # Positive canvas height [inches].
DPI=180                                                               # PNG resolution [pixels/inch].
CMAP="Reds"                                                           # Matplotlib colormap; affects display only.
VMIN=0                                                                # Display lower limit [% Flood / valid classes].
VMAX=100                                                              # Display upper limit [%]; outside values saturate.
GAMMA=0.55                                                            # Positive PowerNorm exponent; 1 gives linear display.
SHOW_OSM=1                                                            # 1: OSM context; 0: omit tile requests.

# ----------------------------------------------------------------------
# User settings end here.
# ----------------------------------------------------------------------

export MPLCONFIGDIR="$TUTORIAL_DIR/Atlantis/analysis/logs/matplotlib"
# The guarded array expansion below also supports an empty list under Bash 3.2 with set -u.
EXTRA_ARGS=()
if [[ "${1:-}" == "--figure-only" ]]; then EXTRA_ARGS+=(--render-only);
elif [[ "$#" -gt 0 ]]; then printf 'Usage: %s [--figure-only]\n' "$0" >&2; exit 2; fi
if [[ "$SHOW_OSM" == "0" ]]; then EXTRA_ARGS+=(--no-osm); fi
"$PYTHON_CMD" "$TUTORIAL_DIR/script/f03c-flood_fraction_1min.py"  \
    --input "$INPUT" \
    --domain-config "$DOMAIN_CONFIG" \
    --output "$OUTPUT" \
    --coverage-output "$COVERAGE_OUTPUT"  \
    --impact-locations "$IMPACT_LOCATIONS" \
    --focus-areas "$FOCUS_AREAS" \
    --figure-output "$FIGURE_OUTPUT"  \
    --map-dir "$MAP_DIR" \
    --tile-cache "$TILE_CACHE" \
    --fig-width "$FIG_WIDTH" \
    --fig-height "$FIG_HEIGHT"  \
    --dpi "$DPI" \
    --cmap "$CMAP" \
    --vmin "$VMIN" \
    --vmax "$VMAX" \
    --gamma "$GAMMA" ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}
