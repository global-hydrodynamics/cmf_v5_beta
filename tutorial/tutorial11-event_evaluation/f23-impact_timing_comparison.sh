#!/usr/bin/env bash
# Generate the Step 23 timing comparison figures from saved CSV handoffs.
set -euo pipefail
export MPLBACKEND=Agg
export MPLCONFIGDIR="${MPLCONFIGDIR:-${TMPDIR:-/tmp}/cama-mplconfig}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON="${PYTHON:-$REPO_ROOT/.venv/bin/python}"
TIMESERIES_CSV="$SCRIPT_DIR/metadata/23_impact_model_timeseries.csv"
COMPARISON_CSV="$SCRIPT_DIR/metadata/23_impact_timing_comparison.csv"
HYDROGRAPHS_OUTPUT="$SCRIPT_DIR/figure/f23a-impact_hydrographs.png"
SUMMARY_OUTPUT="$SCRIPT_DIR/figure/f23b-impact_timing_summary.png"
# Fig23b display range, event note and Fig1 palette reference.
SUMMARY_SETTINGS="$SCRIPT_DIR/metadata/23_timing_figure_settings.json"

if [[ ! -f "$TIMESERIES_CSV" || ! -f "$COMPARISON_CSV" ]]; then
  printf 'Missing Step 23 CSV outputs; run s23-impact_timing_comparison.sh first.\n' >&2
  exit 2
fi

"$PYTHON" "$SCRIPT_DIR/script/f23-impact_timing_comparison.py" \
  --timeseries-csv "$TIMESERIES_CSV" \
  --comparison-csv "$COMPARISON_CSV" \
  --hydrographs-output "$HYDROGRAPHS_OUTPUT" \
  --summary-output "$SUMMARY_OUTPUT" \
  --summary-settings "$SUMMARY_SETTINGS" \
  "$@"
