#!/usr/bin/env bash
set -euo pipefail

# Internal path anchors; user paths below are independent of the caller's directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
TUTORIAL_DIR="$SCRIPT_DIR"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"

# User settings
# ----------------------------------------------------------------------
PYTHON="${PYTHON:-$REPO_ROOT/.venv/bin/python}"                       # Python with required libraries; existing PYTHON override is supported.
TIMESERIES_CSV="$SCRIPT_DIR/metadata/22_hydrograph_timeseries.csv"    # Saved model/observation records; no extraction here.
SUMMARY_JSON="$SCRIPT_DIR/metadata/22_hydrograph_comparison_summary.json" # Authoritative analysis interval/provenance.
OUTPUT="$SCRIPT_DIR/figure/f22-hydrograph_comparison.png"             # Output PNG path.
DISPLAY_START=""                                                      # Blank: summary interval; otherwise ISO nominal display start only.
DISPLAY_END=""                                                        # Blank: summary interval; otherwise ISO nominal display end only.
YMIN=0                                                                # Display lower limit [model m3/s; observation unit unspecified].
YMAX=""                                                               # Blank: automatic upper limit; otherwise display values.
MODEL_COLOR="#2369a1"                                                 # Matplotlib model-line color.
OBSERVATION_COLOR="#d87524"                                           # Matplotlib observation-line color.
FIG_WIDTH=11                                                          # Canvas width [inches].
FIG_HEIGHT=8                                                          # Positive canvas height [inches].
DPI=180                                                               # PNG resolution [pixels/inch].

# ----------------------------------------------------------------------
# User settings end here.
# ----------------------------------------------------------------------

if [[ ! -f "$TIMESERIES_CSV" ]]; then
  printf 'Missing %s; run s22-extract_hydrograph.sh first.\n' "$TIMESERIES_CSV" >&2
  exit 2
fi

export MPLBACKEND=Agg MPLCONFIGDIR="${MPLCONFIGDIR:-${TMPDIR:-/tmp}/cama-mplconfig}"
# The guarded array expansion below also supports an empty list under Bash 3.2 with set -u.
EXTRA_ARGS=()
if [[ -n "$DISPLAY_START" ]]; then EXTRA_ARGS+=(--display-start "$DISPLAY_START"); fi
if [[ -n "$DISPLAY_END" ]]; then EXTRA_ARGS+=(--display-end "$DISPLAY_END"); fi
if [[ -n "$YMAX" ]]; then EXTRA_ARGS+=(--ymax "$YMAX"); fi
"$PYTHON" "$SCRIPT_DIR/script/f22-hydrograph_comparison.py"  \
    --tutorial-dir "$SCRIPT_DIR" \
    --timeseries-csv "$TIMESERIES_CSV" \
    --summary-json "$SUMMARY_JSON" \
    --output "$OUTPUT"  \
    --fig-width "$FIG_WIDTH" \
    --fig-height "$FIG_HEIGHT" \
    --dpi "$DPI" \
    --ymin "$YMIN"  \
    --model-color "$MODEL_COLOR" \
    --observation-color "$OBSERVATION_COLOR" ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}
