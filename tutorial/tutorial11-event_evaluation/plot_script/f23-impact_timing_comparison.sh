#!/usr/bin/env bash
set -euo pipefail

# Internal path anchors; user paths below are independent of the caller's directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
TUTORIAL_DIR="$(CDPATH= cd "$SCRIPT_DIR/.." && pwd -P)"
REPO_ROOT="$(cd "$TUTORIAL_DIR/../.." && pwd -P)"

# User settings
# ----------------------------------------------------------------------
PYTHON="${PYTHON:-$REPO_ROOT/.venv/bin/python}"                       # Python with required libraries; existing PYTHON override is supported.
TIMESERIES_CSV="$TUTORIAL_DIR/metadata/23_impact_model_timeseries.csv"  # Saved model series; no extraction/maximum calculation here.
COMPARISON_CSV="$TUTORIAL_DIR/metadata/23_impact_timing_comparison.csv" # Saved report-linked timing comparisons.
HYDROGRAPHS_OUTPUT="$TUTORIAL_DIR/figure/f23a-impact_hydrographs.png"   # Fig23a PNG destination.
SUMMARY_OUTPUT="$TUTORIAL_DIR/figure/f23b-impact_timing_summary.png"    # Fig23b PNG destination.
SUMMARY_SETTINGS="$TUTORIAL_DIR/metadata/23_timing_figure_settings.json" # Fig23b authoritative UTC display range, labels, palette and layout/DPI JSON.
HYDROGRAPH_WIDTH=15                                                   # Fig23a canvas width [inches].
HYDROGRAPH_ROW_HEIGHT=3                                               # Fig23a height per row [inches].
DPI=200                                                               # Fig23a resolution [pixels/inch]; Fig23b DPI belongs to SUMMARY_SETTINGS.

# ----------------------------------------------------------------------
# User settings end here.
# ----------------------------------------------------------------------

if [[ ! -f "$TIMESERIES_CSV" || ! -f "$COMPARISON_CSV" ]]; then
  printf 'Missing Step 23 CSV outputs; run run_script/s23-impact_timing_comparison.sh first.\n' >&2
  exit 2
fi

export MPLBACKEND=Agg MPLCONFIGDIR="${MPLCONFIGDIR:-${TMPDIR:-/tmp}/cama-mplconfig}"
"$PYTHON" "$TUTORIAL_DIR/script/f23-impact_timing_comparison.py"  \
    --timeseries-csv "$TIMESERIES_CSV" \
    --comparison-csv "$COMPARISON_CSV"  \
    --hydrographs-output "$HYDROGRAPHS_OUTPUT" \
    --summary-output "$SUMMARY_OUTPUT"  \
    --summary-settings "$SUMMARY_SETTINGS" \
    --hydrograph-width "$HYDROGRAPH_WIDTH"  \
    --hydrograph-row-height "$HYDROGRAPH_ROW_HEIGHT" \
    --dpi "$DPI" "$@"
