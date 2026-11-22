#!/usr/bin/env bash
set -euo pipefail

# User settings
PYTHON_CMD="${PYTHON_CMD:-python3}"

TUTORIAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$TUTORIAL_DIR/script/s03c-mosaic_gfm_extent.py"
ARGS=(--tutorial-root "$TUTORIAL_DIR" --force)

echo "Classify and clip the selected native 20 m GFM pass to the Step 2 AOI."
echo "No STAC search or source-data download is performed."

"$PYTHON_CMD" -B "$SCRIPT" "${ARGS[@]}"
