#!/usr/bin/env bash
# Validate selected ECMWF gauge allocations against the current Rhine map.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON="${PYTHON:-$REPO_ROOT/.venv/bin/python}"
MAP_DIR="$REPO_ROOT/map/Rhine_15min"
OUTPUT="$SCRIPT_DIR/metadata/21_gauge_allocation.csv"
IMPACT_OUTPUT="$SCRIPT_DIR/metadata/21_impact_location_allocation.csv"

"$PYTHON" "$SCRIPT_DIR/script/s21-gauge_allocation.py" \
    --tutorial-dir "$SCRIPT_DIR" \
    --map-dir "$MAP_DIR" \
    --output "$OUTPUT" \
    --impact-output "$IMPACT_OUTPUT"

printf 'Gauge allocation table: %s\n' "$OUTPUT"
printf 'Impact-location allocation table: %s\n' "$IMPACT_OUTPUT"
