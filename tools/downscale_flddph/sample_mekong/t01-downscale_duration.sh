#!/usr/bin/env bash
set -eu

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

# User settings: external annual output, Mekong map, simulation year, and outputs.
PYTHON="python3"
SOURCE_NC="${PACKAGE_DIR}/../../../gosh_test/out/mek02/o_flddph2001.nc" # Run gosh_test/mek02 first if absent.
MAPDIR="${PACKAGE_DIR}/../../../map/mekong_15min"
MAP_FORMAT="auto"
START_DATE="2001-01-02"                            # 2001 simulation year, end-of-day CF timestamps.
END_DATE="2002-01-01"                              # Inclusive; annual file has 365 daily records.
WEST=102.0
EAST=108.0
SOUTH=9.0
NORTH=15.0
RES="1min"
MAXDPH=20.0
INTDPH=0.05
PERMANENT_WATER=1
TABLE_NC="${PACKAGE_DIR}/out/flood_duration_table_2001.nc"
OUTPUT_NC="${PACKAGE_DIR}/downscaled/flood_duration_1min_2001.nc"

# User settings end here.

if [[ ! -f "$SOURCE_NC" ]]; then
    printf '[ERROR] Annual input not found: %s\nRun the gosh_test/mek02 2001 simulation or set SOURCE_NC to its o_flddph2001.nc.\n' "$SOURCE_NC" >&2
    exit 1
fi

printf '\n[STEP 1/2] Calculate low-resolution depth-duration table from the annual NetCDF.\n'
"$PYTHON" "$PACKAGE_DIR/script/calc_duration.py" \
    --input "$SOURCE_NC" --output "$TABLE_NC" --map-dir "$MAPDIR" \
    --map-format "$MAP_FORMAT" --start-date "$START_DATE" --end-date "$END_DATE" \
    --max-depth "$MAXDPH" --depth-interval "$INTDPH"

printf '\n[STEP 2/2] Map Duration onto the 1min grid.\n'
"$PYTHON" "$PACKAGE_DIR/script/downscale_duration.py" \
    --table "$TABLE_NC" --map-dir "$MAPDIR" --map-format "$MAP_FORMAT" \
    --resolution "$RES" --west "$WEST" --east "$EAST" --south "$SOUTH" --north "$NORTH" \
    --depth-interval "$INTDPH" --permanent-water "$PERMANENT_WATER" --output "$OUTPUT_NC"

printf '\n[SUCCESS] Created high-resolution flood-duration NetCDF.\nOutput: %s\n' "$OUTPUT_NC"
