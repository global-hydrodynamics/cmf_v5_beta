#!/usr/bin/env bash
set -euo pipefail

# User settings
PYTHON_CMD="python3"

TUTORIAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOMAIN_CONFIG="$TUTORIAL_DIR/metadata/02_domain_selection.json"
ATLANTIS_DIR="$TUTORIAL_DIR/Atlantis"
CATALOGUE_ROOT="$ATLANTIS_DIR/catalogue"

echo "[STEP 1/2] Search daily GFM STAC catalogues and retrieve source orbit metadata."
while IFS=' ' read -r SEARCH_DATE WEST SOUTH EAST NORTH; do
    RUN_DIR="$ATLANTIS_DIR/runs/$SEARCH_DATE"
    CATALOGUE_DIR="$CATALOGUE_ROOT/$SEARCH_DATE"
    echo "  Searching $SEARCH_DATE · bbox $WEST $SOUTH $EAST $NORTH"
    "$PYTHON_CMD" "$TUTORIAL_DIR/script/event_gfm_download.py" \
        --work-dir "$RUN_DIR" \
        --output "$CATALOGUE_DIR" \
        --date "$SEARCH_DATE" --bbox "$WEST" "$SOUTH" "$EAST" "$NORTH" \
        --catalogue-only
done < <("$PYTHON_CMD" - "$DOMAIN_CONFIG" <<'PY'
import json
import sys
from datetime import date, timedelta

with open(sys.argv[1], encoding="utf-8") as stream:
    config = json.load(stream)
period = config["satellite_analysis"]["search_period"]
west, south, east, north = config["satellite_analysis"]["domain"]["bbox_west_south_east_north"]
day, end = date.fromisoformat(period["start_date"]), date.fromisoformat(period["end_date"])
while day <= end:
    print(day.isoformat(), west, south, east, north)
    day += timedelta(days=1)
PY
)

echo "[STEP 2/2] Write the pass inventory, orbit directions and source acquisition footprints."
"$PYTHON_CMD" "$TUTORIAL_DIR/script/s03a-gfm_availability.py" \
    --mode metadata \
    --domain-config "$DOMAIN_CONFIG" \
    --catalogue-root "$CATALOGUE_ROOT" \
    --summary-dir "$ATLANTIS_DIR/summary" \
    --inventory-output "$TUTORIAL_DIR/metadata/03a_satellite_pass_inventory.csv" \
    --orbit-metadata "$TUTORIAL_DIR/metadata/03a_satellite_orbit_metadata.csv" \
    --acquisition-footprints "$TUTORIAL_DIR/metadata/03a_sentinel1_acquisition_footprints.geojson"

echo "Metadata survey complete. No figures or satellite COG assets were downloaded."
