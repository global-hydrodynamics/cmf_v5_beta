#!/usr/bin/env bash
# Render the verified station-to-outlet allocation map.
set -euo pipefail
export MPLBACKEND=Agg

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON="${PYTHON:-$REPO_ROOT/.venv/bin/python}"
MAP_DIR="$REPO_ROOT/map/Rhine_15min"
ALLOCATION="$SCRIPT_DIR/metadata/21_gauge_allocation.csv"
IMPACT_ALLOCATION="$SCRIPT_DIR/metadata/21_impact_location_allocation.csv"
OUTPUT="$SCRIPT_DIR/figure/f21a-gauge_allocation.png"
# Show the priority localities and their final adopted evaluation outlets.
CATCHMENT_EXTENT="6.4,7.5,50.25,51.10"  # west,east,south,north

if [[ ! -f "$ALLOCATION" ]]; then
    printf 'Missing %s; run s21-gauge_allocation.sh first.\n' "$ALLOCATION" >&2
    exit 2
fi
if [[ ! -f "$IMPACT_ALLOCATION" ]]; then
    printf 'Missing %s; run s21-gauge_allocation.sh first.\n' "$IMPACT_ALLOCATION" >&2
    exit 2
fi

"$PYTHON" "$SCRIPT_DIR/script/f21-gauge_allocation.py" \
    --tutorial-dir "$SCRIPT_DIR" \
    --map-dir "$MAP_DIR" \
    --allocation-csv "$ALLOCATION" \
    --impact-allocation-csv "$IMPACT_ALLOCATION" \
    --output "$OUTPUT" \
    --catchment-output "$SCRIPT_DIR/figure/f21b-catchment_allocation.png" \
    --catchment-extent "$CATCHMENT_EXTENT"

printf 'Gauge allocation figure: %s\n' "$OUTPUT"
