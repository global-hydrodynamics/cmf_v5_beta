#!/usr/bin/env bash
# Render the Step 22 three-station model–observation hydrograph Figure.
set -euo pipefail
export MPLBACKEND=Agg
export MPLCONFIGDIR="${MPLCONFIGDIR:-${TMPDIR:-/tmp}/cama-mplconfig}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON="${PYTHON:-$REPO_ROOT/.venv/bin/python}"
TIMESERIES_CSV="$SCRIPT_DIR/metadata/22_hydrograph_timeseries.csv"
SUMMARY_JSON="$SCRIPT_DIR/metadata/22_hydrograph_comparison_summary.json"
OUTPUT="$SCRIPT_DIR/figure/f22-hydrograph_comparison.png"

if [[ ! -f "$TIMESERIES_CSV" ]]; then
  printf 'Missing %s; run s22-extract_hydrograph.sh first.\n' "$TIMESERIES_CSV" >&2
  exit 2
fi

"$PYTHON" "$SCRIPT_DIR/script/f22-hydrograph_comparison.py" \
  --tutorial-dir "$SCRIPT_DIR" \
  --timeseries-csv "$TIMESERIES_CSV" \
  --summary-json "$SUMMARY_JSON" \
  --output "$OUTPUT"
