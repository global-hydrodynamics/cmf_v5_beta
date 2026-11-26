#!/bin/sh
set -eu

PYTHON_CMD="${PYTHON_CMD:-python3}"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
cd "$SCRIPT_DIR"

if [ "$#" -lt 3 ] || [ "$#" -gt 4 ] || [ "$1" != "xy" ]; then
    printf 'Usage: %s xy IX IY [OUTPUT.nc]\n' "${0##*/}" >&2
    printf 'IX and IY are one-based CaMa-Flood grid indices.\n' >&2
    exit 2
fi

IX=$2
IY=$3
OUTPUT=${4:-"../upbasin-${IX}-${IY}.nc"}

printf 'Selected river cell (1-based, Fortran): IX=%s, IY=%s\n' "$IX" "$IY"
"$PYTHON_CMD" "$CODE_DIR/analysis_upbasin.py" "$IX" "$IY" "$OUTPUT"
printf 'Output file: %s\n' "$OUTPUT"
