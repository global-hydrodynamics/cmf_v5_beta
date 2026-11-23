#!/usr/bin/env bash
# Render the verified station-to-outlet allocation map.
set -euo pipefail
export MPLBACKEND=Agg

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON="${PYTHON:-$REPO_ROOT/.venv/bin/python}"
MAP_DIR="$REPO_ROOT/map/Rhine_15min"
ALLOCATION="$SCRIPT_DIR/metadata/21_gauge_allocation.csv"
OUTPUT="$SCRIPT_DIR/figure/f21-gauge_allocation.png"

if [[ ! -f "$ALLOCATION" ]]; then
    printf 'Missing %s; run s21-gauge_allocation.sh first.\n' "$ALLOCATION" >&2
    exit 2
fi

"$PYTHON" "$SCRIPT_DIR/script/f21-gauge_allocation.py" \
    --tutorial-dir "$SCRIPT_DIR" \
    --map-dir "$MAP_DIR" \
    --allocation-csv "$ALLOCATION" \
    --output "$OUTPUT"

printf 'Gauge allocation figure: %s\n' "$OUTPUT"
