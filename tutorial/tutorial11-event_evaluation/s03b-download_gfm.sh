#!/usr/bin/env bash
set -euo pipefail

# User settings
PYTHON_CMD="python3"
DATE="2021-07-15"
PASS_ID="S1A_o038784_dt049389"
WEST=4.0
SOUTH=49.0
EAST=8.0
NORTH=52.0
WORKERS=2

TUTORIAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ATLANTIS_DIR="$TUTORIAL_DIR/Atlantis"
CATALOGUE_DIR="$ATLANTIS_DIR/catalogue/$DATE"
RUN_DIR="$ATLANTIS_DIR/runs/download_$PASS_ID"

if [[ ! -s "$CATALOGUE_DIR/metadata/stac_items.json" || \
      ! -s "$TUTORIAL_DIR/metadata/satellite_pass_inventory.csv" ]]; then
    printf 'Step 3a catalogue or pass inventory is missing. Run bash s03a-satellite_availability.sh first.\n' >&2
    exit 1
fi
if ! awk -F, -v pass="$PASS_ID" -v date="$DATE" \
        '$1 == pass && $2 == "S1A" && $5 == "DESCENDING" && substr($7, 1, 10) == date { found=1 } END { exit !found }' \
        "$TUTORIAL_DIR/metadata/satellite_pass_inventory.csv"; then
    printf 'PASS_ID %s is not in the current Step 3a inventory. Review the inventory or set PASS_ID explicitly.\n' "$PASS_ID" >&2
    exit 1
fi

echo "Download selected GFM pass $PASS_ID ($DATE; native 20 m COGs)."
echo "Layers: ensemble_flood_extent, ensemble_water_extent, reference_water_mask, exclusion_mask"
"$PYTHON_CMD" "$TUTORIAL_DIR/script/s01-download_gfm.py" \
    --work-dir "$RUN_DIR" \
    --output "$CATALOGUE_DIR" \
    --date "$DATE" --bbox "$WEST" "$SOUTH" "$EAST" "$NORTH" \
    --group "$PASS_ID" --workers "$WORKERS"

echo "Native GFM download complete. No reprojection, mosaic conversion or classification was run."
