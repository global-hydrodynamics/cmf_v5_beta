#!/usr/bin/env bash
set -eu

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

# User settings: input formats, source snapshot, map format, options and output grid.
PYTHON="python3"                                      # Python with NumPy and netCDF4.
MAPDIR="${PACKAGE_DIR}/../../map/mekong_15min"        # Coarse and high-resolution CaMa-Flood map root.
INPUT_FORMAT="auto"                                  # auto / netcdf / binary.
MAP_FORMAT="auto"                                    # auto / netcdf / binary; auto prefers NetCDF.
TRIBUTARY_FILL=1                                      # 1: tributary/backwater adjustments; 0: basic downscaling.
PERMANENT_WATER=1                                     # 1: apply 0.1 m river-width minimum; 0: omit it.
INPUT_FILE="${PACKAGE_DIR}/sample_mekong/out/flddph_2001-09-01.nc" # NetCDF snapshot or single-record Float32 Binary.
OUTPUT_NC="${PACKAGE_DIR}/sample_mekong/downscaled/flddph_1min_2001-09-01.nc" # High-resolution result.
WEST=102.0
EAST=108.0
SOUTH=9.0
NORTH=15.0
RES="1min"

# User settings end here.

"$PYTHON" "$PACKAGE_DIR/script/downscale_flddph.py" \
    --input "$INPUT_FILE" --input-format "$INPUT_FORMAT" \
    --map-dir "$MAPDIR" --map-format "$MAP_FORMAT" --resolution "$RES" \
    --west "$WEST" --east "$EAST" --south "$SOUTH" --north "$NORTH" \
    --tributary-fill "$TRIBUTARY_FILL" --permanent-water "$PERMANENT_WATER" \
    --output "$OUTPUT_NC"

printf '[SUCCESS] Created high-resolution flood-depth NetCDF: %s\n' "$OUTPUT_NC"
