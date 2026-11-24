#!/usr/bin/env bash
set -euo pipefail

# Internal path anchors; user paths below are independent of the caller's directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
TUTORIAL_DIR="$(CDPATH= cd "$SCRIPT_DIR/.." && pwd -P)"
REPO_ROOT="$(cd "$TUTORIAL_DIR/../.." && pwd -P)"

# User settings
# ----------------------------------------------------------------------
PYTHON="${PYTHON:-$REPO_ROOT/.venv/bin/python}"                       # Python with required libraries; existing PYTHON override is supported.
MAP_DIR="$REPO_ROOT/map/Rhine_15min"                                  # Matching coarse/high-resolution map root.
ALLOCATION="$TUTORIAL_DIR/metadata/21_gauge_allocation.csv"             # Step21 station allocation handoff.
IMPACT_ALLOCATION="$TUTORIAL_DIR/metadata/21_impact_location_allocation.csv" # Final geographic/direct/proxy allocations; no reallocation here.
OUTPUT="$TUTORIAL_DIR/figure/f21a-gauge_allocation.png"                 # Regional allocation PNG destination.
CATCHMENT_OUTPUT="$TUTORIAL_DIR/figure/f21b-catchment_allocation.png"   # Unit-catchment review PNG destination.
CATCHMENT_EXTENT="6.4,7.5,50.25,51.10"                                # Catchment view [west,east,south,north degrees]; note ordering.
FIG_WIDTH=13.0                                                        # Canvas width [inches].
FIG_HEIGHT=9.2                                                        # Positive canvas height [inches].
DPI=200                                                               # PNG resolution [pixels/inch].

# ----------------------------------------------------------------------
# User settings end here.
# ----------------------------------------------------------------------

if [[ ! -f "$ALLOCATION" ]]; then
    printf 'Missing %s; run run_script/s21-gauge_allocation.sh first.\n' "$ALLOCATION" >&2
    exit 2
fi
if [[ ! -f "$IMPACT_ALLOCATION" ]]; then
    printf 'Missing %s; run run_script/s21-gauge_allocation.sh first.\n' "$IMPACT_ALLOCATION" >&2
    exit 2
fi

export MPLBACKEND=Agg
"$PYTHON" "$TUTORIAL_DIR/script/f21-gauge_allocation.py"  \
    --tutorial-dir "$TUTORIAL_DIR" \
    --map-dir "$MAP_DIR" \
    --allocation-csv "$ALLOCATION"  \
    --impact-allocation-csv "$IMPACT_ALLOCATION" \
    --output "$OUTPUT" \
    --catchment-output "$CATCHMENT_OUTPUT"  \
    --catchment-extent "$CATCHMENT_EXTENT" \
    --fig-width "$FIG_WIDTH" \
    --fig-height "$FIG_HEIGHT" \
    --dpi "$DPI"
