#!/bin/sh
# Regenerate the repository sample from the optional global NetCDF dataset.
set -eu

# User settings

# Inclusive daily period and grid-cell boundaries, in degrees east/north.
WEST=90
EAST=110
SOUTH=5
NORTH=35
START_DATE="2000-01-01"
END_DATE="2000-02-29"

# ================================================================
# User settings end here
# ================================================================

# Command substitution locates this script independently of the caller's directory.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
python3 "$SCRIPT_DIR/../tools/extract_ELSE_GPCC.py" \
    --input-dir "$SCRIPT_DIR/../ELSE_GPCC" --output-dir "$SCRIPT_DIR/runoff" \
    --west "$WEST" --east "$EAST" --south "$SOUTH" --north "$NORTH" \
    --start-date "$START_DATE" --end-date "$END_DATE" --format binary --file-unit month
