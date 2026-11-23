#!/usr/bin/env bash
set -eu

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

# User settings: source snapshot, target map, output domain and resolution.
PYTHON="python3"                                      # Python with NumPy and netCDF4.
MAPDIR="${PACKAGE_DIR}/../../../../map/mekong_15min" # Coarse and high-resolution CaMa-Flood map root.
INPUT_NC="${PACKAGE_DIR}/out/flddph_2001-09-01.nc" # 2D flddph or one-record NetCDF.
OUTPUT_NC="${PACKAGE_DIR}/downscaled/flddph_1min_2001-09-01.nc" # High-resolution result.
WEST=102.0                                              # Western output edge [degrees east].
EAST=108.0                                              # Eastern output edge [degrees east].
SOUTH=9.0                                               # Southern output edge [degrees north].
NORTH=15.0                                              # Northern output edge [degrees north].
RES="1min"                                              # Existing high-resolution map directory/tag.

# User settings end here.

printf '\n[STEP 1/1] Downscale one 2D flood-depth field.\n'
"$PYTHON" "$PACKAGE_DIR/script/downscale_flddph.py" \
    --input "$INPUT_NC" --map-dir "$MAPDIR" --resolution "$RES" \
    --west "$WEST" --east "$EAST" --south "$SOUTH" --north "$NORTH" \
    --output "$OUTPUT_NC"

printf '\n[SUCCESS] Created high-resolution flood-depth NetCDF.\n'
printf 'Output: %s\n' "$OUTPUT_NC"
