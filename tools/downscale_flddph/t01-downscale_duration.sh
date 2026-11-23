#!/usr/bin/env bash
set -eu

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

# User settings: annual daily input, model map, period, output grid, and Duration method.
PYTHON="python3"
INPUT_FILE="/path/to/o_flddph2001.nc"             # Daily CF NetCDF, flddph(time,lat,lon).
MAPDIR="/path/to/map/mekong_15min"                # Matching CaMa-Flood map directory.
MAP_FORMAT="auto"                                 # auto / netcdf / binary.
START_DATE="2001-01-02"                            # First CF timestamp; day-end labels for 2001 run.
END_DATE="2002-01-01"                              # Inclusive last CF timestamp; 365 records total.
WEST=102.0                                          # Output west edge [degrees east].
EAST=108.0                                          # Output east edge [degrees east].
SOUTH=9.0                                           # Output south edge [degrees north].
NORTH=15.0                                          # Output north edge [degrees north].
RES="1min"                                         # Existing high-resolution map.
MAXDPH=20.0                                         # Maximum threshold [m].
INTDPH=0.05                                         # Threshold interval [m].
PERMANENT_WATER=1                                   # 1: emit separate rivwth mask; 0: all zero.
TABLE_NC="${PACKAGE_DIR}/sample_mekong/out/flood_duration_table_2001.nc"
OUTPUT_NC="${PACKAGE_DIR}/sample_mekong/downscaled/flood_duration_1min_2001.nc"

# User settings end here.

if [[ ! -f "$INPUT_FILE" ]]; then
    printf '[ERROR] Daily input not found: %s\nSet INPUT_FILE to an existing annual flddph NetCDF.\n' "$INPUT_FILE" >&2
    exit 1
fi

printf '\n[STEP 1/2] Calculate low-resolution depth-duration table.\n'
"$PYTHON" "$PACKAGE_DIR/script/calc_duration.py" \
    --input "$INPUT_FILE" --output "$TABLE_NC" --map-dir "$MAPDIR" \
    --map-format "$MAP_FORMAT" --start-date "$START_DATE" --end-date "$END_DATE" \
    --max-depth "$MAXDPH" --depth-interval "$INTDPH"

printf '\n[STEP 2/2] Map Duration onto the high-resolution grid.\n'
"$PYTHON" "$PACKAGE_DIR/script/downscale_duration.py" \
    --table "$TABLE_NC" --map-dir "$MAPDIR" --map-format "$MAP_FORMAT" \
    --resolution "$RES" --west "$WEST" --east "$EAST" --south "$SOUTH" --north "$NORTH" \
    --depth-interval "$INTDPH" --permanent-water "$PERMANENT_WATER" --output "$OUTPUT_NC"

printf '\n[SUCCESS] Created high-resolution flood-duration NetCDF.\nOutput: %s\n' "$OUTPUT_NC"
