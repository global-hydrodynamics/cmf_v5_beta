#!/usr/bin/env bash
# Inspection only; requires the separately acquired local morning GFM products.
set -euo pipefail
# User settings: paths are independent of the caller's working directory.
WORK_DIR="${ATLANTIS_WORK_DIR:-$HOME/work/Atlantis}"
PYTHON="${ATLANTIS_PYTHON:-$WORK_DIR/source/.pixi/envs/default/bin/python}"
DATA_DIR="$WORK_DIR/data/Rhine_2021_3sec"
GROUP="S1A_o038784_dt049389"
FIG_HEIGHT=6.6
DPI=160
SCRIPT_DIR=$("$PYTHON" -B -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve().parent)' "${BASH_SOURCE[0]}")
OUTPUT="$SCRIPT_DIR/figure/gfm_20210715_3sec_validation.png"
export PYTHONDONTWRITEBYTECODE=1 GDAL_PAM_ENABLED=NO PROJ_NETWORK=OFF
export MPLCONFIGDIR="$WORK_DIR/logs/matplotlib"
"$PYTHON" -B "$SCRIPT_DIR/script/f01-gfm_3sec_validation.py" \
  --work-dir "$WORK_DIR" --data "$DATA_DIR" --group "$GROUP" \
  --output "$OUTPUT" --fig-height "$FIG_HEIGHT" --dpi "$DPI"
