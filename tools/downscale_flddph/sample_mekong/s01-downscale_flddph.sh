#!/usr/bin/env bash
set -eu

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

# User settings: input formats, source snapshot, map format, options and output grid.
PYTHON="python3"                                      # Python with NumPy and netCDF4.
SOURCE_NC="${PACKAGE_DIR}/../../../gosh_test/out/mek02/o_flddph2001.nc" # Source for the selected snapshot.
MAPDIR="${PACKAGE_DIR}/../../../map/mekong_15min"    # Coarse and high-resolution CaMa-Flood map root.
INPUT_FORMAT="auto"                                  # auto / netcdf / binary.
MAP_FORMAT="auto"                                    # auto / netcdf / binary; auto prefers NetCDF.
TRIBUTARY_FILL=1                                      # 1: tributary/backwater adjustments; 0: basic downscaling.
PERMANENT_WATER=1                                     # 1: apply 0.1 m river-width minimum; 0: omit it.
INPUT_FILE="${PACKAGE_DIR}/out/flddph_2001-09-01.nc" # NetCDF snapshot or single-record Float32 Binary.
OUTPUT_NC="${PACKAGE_DIR}/downscaled/flddph_1min_2001-09-01.nc" # High-resolution result.
WEST=102.0                                              # Western output edge [degrees east].
EAST=108.0                                              # Eastern output edge [degrees east].
SOUTH=9.0                                               # Southern output edge [degrees north].
NORTH=15.0                                              # Northern output edge [degrees north].
RES="1min"                                              # Existing high-resolution map directory/tag.

# User settings end here.

if [[ ! -f "$INPUT_FILE" ]]; then
    if [[ ! -f "$SOURCE_NC" ]]; then
        printf '[ERROR] Snapshot and source annual file are both missing.\nSnapshot: %s\nAnnual file: %s\nRun gosh_test/mek02 or set SOURCE_NC.\n' "$INPUT_FILE" "$SOURCE_NC" >&2
        exit 1
    fi
    mkdir -p "$(dirname "$INPUT_FILE")"
    printf '\n[STEP 1/2] Extract the 2001-09-01 CF-time snapshot.\n'
    "$PYTHON" "$PACKAGE_DIR/script/aggregate_flddph.py" \
        --input "$SOURCE_NC" --output "$INPUT_FILE" --mode snapshot --time 2001-09-01T00:00:00
else
    printf '[INFO] Reusing existing snapshot: %s\n' "$INPUT_FILE"
fi

printf '\n[STEP 2/2] Downscale one 2D flood-depth field.\n'
"$PYTHON" "$PACKAGE_DIR/script/downscale_flddph.py" \
    --input "$INPUT_FILE" --input-format "$INPUT_FORMAT" \
    --map-dir "$MAPDIR" --map-format "$MAP_FORMAT" --resolution "$RES" \
    --west "$WEST" --east "$EAST" --south "$SOUTH" --north "$NORTH" \
    --tributary-fill "$TRIBUTARY_FILL" --permanent-water "$PERMANENT_WATER" \
    --output "$OUTPUT_NC"

printf '\n[SUCCESS] Created high-resolution flood-depth NetCDF.\n'
printf 'Output: %s\n' "$OUTPUT_NC"
