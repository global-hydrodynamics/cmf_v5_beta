#!/usr/bin/env bash
set -euo pipefail

# Internal path anchors; user paths below are independent of the caller's directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
TUTORIAL_DIR="$(CDPATH= cd "$SCRIPT_DIR/.." && pwd -P)"
REPO_ROOT="$(cd "$TUTORIAL_DIR/../.." && pwd -P)"

# User settings
# ----------------------------------------------------------------------
PYTHON="$REPO_ROOT/.venv/bin/python"                                  # Python with Matplotlib, NumPy and netCDF4.
METADATA="$TUTORIAL_DIR/metadata/24_downscaling_verification.json"    # Authoritative input file, selected time and bounds; no recomputation.
OUTPUT="$TUTORIAL_DIR/figure/f24-inundation_1min.png"                 # Output PNG path.
CMAP="YlGnBu"                                                         # Matplotlib continuous depth colormap.
VMIN=0                                                                # Display minimum simulated depth [m].
VMAX=10                                                               # Display maximum depth [m]; larger values use upper colorbar extension.
FIG_WIDTH=8.4                                                         # Canvas width [inches].
FIG_HEIGHT=7.2                                                        # Positive canvas height [inches].
DPI=200                                                               # PNG resolution [pixels/inch].

# ----------------------------------------------------------------------
# User settings end here.
# ----------------------------------------------------------------------

export MPLBACKEND=Agg MPLCONFIGDIR="${MPLCONFIGDIR:-${TMPDIR:-/tmp}/cama-mplconfig}"
"$PYTHON" "$TUTORIAL_DIR/script/f24-inundation_1min.py" \
    --tutorial-dir "$TUTORIAL_DIR"  \
    --metadata "$METADATA" \
    --output "$OUTPUT" \
    --cmap "$CMAP" \
    --vmin "$VMIN" \
    --vmax "$VMAX"  \
    --fig-width "$FIG_WIDTH" \
    --fig-height "$FIG_HEIGHT" \
    --dpi "$DPI"
