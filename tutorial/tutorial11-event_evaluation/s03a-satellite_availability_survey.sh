#!/usr/bin/env bash
set -euo pipefail

# User settings
PYTHON_CMD="python3"
TUTORIAL_DIR="tutorial/tutorial11-event_evaluation"
DOMAIN_CONFIG="$TUTORIAL_DIR/metadata/domain_selection.json"
ATLANTIS_OUTPUT="$TUTORIAL_DIR/Atlantis"
MAP_DIR="map/glb_15min"
TILE_CACHE="$HOME/.cache/cmf_flood_osm_tiles"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

echo "[STEP 1/3] Search daily GFM catalogues from Step 2 domain_selection.json."
while IFS=' ' read -r SEARCH_DATE WEST SOUTH EAST NORTH; do
    RUN_DIR="$ATLANTIS_OUTPUT/runs/$SEARCH_DATE"
    echo "  Searching $SEARCH_DATE · bbox $WEST $SOUTH $EAST $NORTH"
    "$PYTHON_CMD" "$TUTORIAL_DIR/scripts/s01-download_gfm.py" \
        --work-dir "$RUN_DIR" \
        --output "$ATLANTIS_OUTPUT/catalogue/$SEARCH_DATE" \
        --date "$SEARCH_DATE" --bbox "$WEST" "$SOUTH" "$EAST" "$NORTH" \
        --catalogue-only
done < <("$PYTHON_CMD" - "$DOMAIN_CONFIG" <<'PY'
import json
import sys
from datetime import date, timedelta

config = json.load(open(sys.argv[1], encoding="utf-8"))
period = config["satellite_analysis"]["search_period"]
west, south, east, north = config["satellite_analysis"]["domain"]["bbox_west_south_east_north"]
day, end = date.fromisoformat(period["start_date"]), date.fromisoformat(period["end_date"])
while day <= end:
    print(day.isoformat(), west, south, east, north)
    day += timedelta(days=1)
PY
)

echo "[STEP 2/3] Summarize passes and render same-extent footprint comparison maps."
"$PYTHON_CMD" "$TUTORIAL_DIR/scripts/s03a-summarize_gfm_availability.py" \
    --domain-config "$DOMAIN_CONFIG" --catalogue-root "$ATLANTIS_OUTPUT/catalogue" \
    --summary-dir "$ATLANTIS_OUTPUT/summary" \
    --inventory-output "$TUTORIAL_DIR/metadata/satellite_pass_inventory.csv" \
    --map-dir "$MAP_DIR" \
    --tile-cache "$TILE_CACHE" --figure-dir "$TUTORIAL_DIR/figure"

echo "[STEP 3/3] Review outputs. No GFM COG assets were downloaded."
ls -lh "$TUTORIAL_DIR/metadata/satellite_pass_inventory.csv" \
    "$TUTORIAL_DIR"/figure/f03a-gfm-pass-footprints-*.png
