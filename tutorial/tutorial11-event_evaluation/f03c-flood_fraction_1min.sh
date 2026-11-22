#!/usr/bin/env bash
set -euo pipefail

# User settings
PYTHON_CMD="${PYTHON_CMD:-python3}"

TUTORIAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$TUTORIAL_DIR/../.." && pwd)"
ATLANTIS_DIR="$TUTORIAL_DIR/Atlantis"
ANALYSIS_DIR="$ATLANTIS_DIR/analysis"
mkdir -p "$ANALYSIS_DIR/logs/matplotlib"
export MPLCONFIGDIR="$ANALYSIS_DIR/logs/matplotlib"

EXTRA_ARGS=()
if [[ "${1:-}" == "--figure-only" ]]; then
    EXTRA_ARGS+=(--render-only)
elif [[ "$#" -gt 0 ]]; then
    printf 'Usage: bash f03c-flood_fraction_1min.sh [--figure-only]\n' >&2
    exit 2
fi

"$PYTHON_CMD" "$TUTORIAL_DIR/script/s03c-flood_fraction_1min.py" \
    --input "$TUTORIAL_DIR/observation/GFM_extent/GFM_S1A_20210715_o038784_dt049389_extent20m.tif" \
    --domain-config "$TUTORIAL_DIR/metadata/02_domain_selection.json" \
    --output "$TUTORIAL_DIR/observation/GFM_extent/GFM_S1A_20210715_o038784_dt049389_floodfrac_1min.tif" \
    --coverage-output "$ANALYSIS_DIR/GFM_S1A_20210715_o038784_dt049389_valid_pixel_count_1min.tif" \
    --impact-locations "$TUTORIAL_DIR/metadata/01_impact_locations.csv" \
    --focus-areas "$TUTORIAL_DIR/metadata/f03c_focus_areas.json" \
    --figure-output "$TUTORIAL_DIR/figure/f03c-gfm_flood_fraction_1min.png" \
    --map-dir "$REPO_ROOT/map/glb_15min" \
    --tile-cache "$HOME/.cache/cmf_flood_osm_tiles" \
    "${EXTRA_ARGS[@]}"
