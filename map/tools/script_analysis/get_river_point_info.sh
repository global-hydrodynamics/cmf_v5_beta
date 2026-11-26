#!/bin/sh
set -eu

PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
CODE_DIR="$CMF_V50_ROOT/map/tools/code"

"$PYTHON_CMD" "$CODE_DIR/analysis_river_point_info.py" "$@"
