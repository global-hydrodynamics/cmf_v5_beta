#!/usr/bin/env bash
set -euo pipefail

# Internal path anchors; user paths below are independent of the caller's directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
TUTORIAL_DIR="$SCRIPT_DIR"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
_PYTHON_DEFAULT="$REPO_ROOT/.venv/bin/python"
if [[ ! -x "$_PYTHON_DEFAULT" ]]; then _PYTHON_DEFAULT="python3"; fi

# User settings
# ----------------------------------------------------------------------
PYTHON="${PYTHON:-$_PYTHON_DEFAULT}"                                  # Existing PYTHON override; default .venv, otherwise python3 (unchanged fallback).
STATION_FILE="$TUTORIAL_DIR/observation/stations_data/allstations.csv" # Station identity table; joined by Id, not row order.
SERIES_FILE="$TUTORIAL_DIR/observation/stations_data/Qobs_06_2021_st153_63_28.csv" # Supplied three-station six-hour CSV; unit/timezone remain unspecified.
OUTPUT="$TUTORIAL_DIR/figure/f04-observed_discharge.png"              # Output PNG path.
START="2021-07-01T00:00:00"                                           # Exclusive start in unmodified source time labels; no UTC assumption.
END="2021-08-01T00:00:00"                                             # Inclusive end in source time labels (interval-end convention).
YMIN=0                                                                # Display lower limit [source unit unspecified].
YMAX=""                                                               # Blank: automatic shared upper limit; otherwise source-value units.
FIG_WIDTH=11.5                                                        # Canvas width [inches].
FIG_HEIGHT=8                                                          # Positive canvas height [inches].
DPI=180                                                               # PNG resolution [pixels/inch].

# ----------------------------------------------------------------------
# User settings end here.
# ----------------------------------------------------------------------

# The guarded array expansion below also supports an empty list under Bash 3.2 with set -u.
EXTRA_ARGS=()
if [[ -n "$YMAX" ]]; then EXTRA_ARGS+=(--ymax "$YMAX"); fi
"$PYTHON" "$TUTORIAL_DIR/script/f04-observed_discharge.py"  \
    --tutorial-dir "$TUTORIAL_DIR" \
    --station-file "$STATION_FILE" \
    --series-file "$SERIES_FILE"  \
    --output "$OUTPUT" \
    --start "$START" \
    --end "$END" \
    --ymin "$YMIN"  \
    --fig-width "$FIG_WIDTH" \
    --fig-height "$FIG_HEIGHT" \
    --dpi "$DPI" ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}
