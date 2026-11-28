#!/usr/bin/env bash
# Validate selected ECMWF gauge allocations against the current Rhine map.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TUTORIAL_DIR="$(CDPATH= cd "$SCRIPT_DIR/.." && pwd -P)"
REPO_ROOT="$(cd "$TUTORIAL_DIR/../.." && pwd)"
# User settings
# ----------------------------------------------------------------------
PYTHON="${PYTHON:-$REPO_ROOT/.venv/bin/python}" # Python executable; existing env override supported.
MAP_DIR="$TUTORIAL_DIR/map/Rhine_15min" # Tutorial-local matching coarse/high-resolution map root.
OUTPUT="$TUTORIAL_DIR/metadata/21_gauge_allocation.csv" # Gauge allocation CSV destination.
IMPACT_OUTPUT="$TUTORIAL_DIR/metadata/21_impact_location_allocation.csv" # Report-linked impact allocation CSV destination.
# ----------------------------------------------------------------------
# User settings end here.
# ----------------------------------------------------------------------

"$PYTHON" "$TUTORIAL_DIR/script/s21-gauge_allocation.py" \
    --tutorial-dir "$TUTORIAL_DIR" \
    --map-dir "$MAP_DIR" \
    --output "$OUTPUT" \
    --impact-output "$IMPACT_OUTPUT" \
    "$@"

printf 'Gauge allocation table: %s\n' "$OUTPUT"
printf 'Impact-location allocation table: %s\n' "$IMPACT_OUTPUT"
