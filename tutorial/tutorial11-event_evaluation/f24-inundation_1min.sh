#!/usr/bin/env bash
set -eu

TUTORIAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "$TUTORIAL_DIR/../.." && pwd -P)"

# User settings: draw the saved Step24 output without recomputing it.
PYTHON="$REPO_ROOT/.venv/bin/python"                     # Matplotlib, NumPy and netCDF4.

# ========================================
# User settings end here.
# ========================================

export MPLBACKEND=Agg
export MPLCONFIGDIR="${TMPDIR:-/tmp}/cama-mplconfig"
"$PYTHON" "$TUTORIAL_DIR/script/f24-inundation_1min.py" --tutorial-dir "$TUTORIAL_DIR"
