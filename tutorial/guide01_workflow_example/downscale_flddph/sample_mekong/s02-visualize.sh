#!/usr/bin/env bash
set -eu

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"

# User settings: input fields, map context, plot extent and display scale.
PYTHON="${CMF_V50_ROOT}/.venv/bin/python"            # Repository Python environment with NumPy, netCDF4 and Matplotlib.
MAPDIR="${PACKAGE_DIR}/../../../../map/mekong_15min" # Matching coarse and high-resolution maps.
INPUT_NC="${PACKAGE_DIR}/out/flddph_2001-09-01.nc" # Native-grid flddph.
DOWNSCALED_NC="${PACKAGE_DIR}/downscaled/flddph_1min_2001-09-01.nc" # Existing result.
FIGURE="${PACKAGE_DIR}/figure/flood_depth_2001-09-01.png" # Figure output path.
WEST=102.0                                              # Western plot edge [degrees east].
EAST=108.0                                              # Eastern plot edge [degrees east].
SOUTH=9.0                                               # Southern plot edge [degrees north].
NORTH=15.0                                              # Northern plot edge [degrees north].
RES="1min"                                              # High-resolution map tag for flddif context.
DEPTH_MIN=0.0                                           # Colorbar minimum [m].
DEPTH_MAX=20.0                                          # Colorbar maximum [m].
FIGURE_WIDTH=12.0                                       # Complete Figure width [inches].
FIGURE_HEIGHT=5.8                                       # Complete Figure height [inches].
DPI=180                                                 # PNG resolution [dots per inch].

# User settings end here.

printf '\n[STEP 1/1] Draw native-grid and downscaled flood depth.\n'
"$PYTHON" "$PACKAGE_DIR/script/visualize_flddph.py" \
    --input "$INPUT_NC" --downscaled "$DOWNSCALED_NC" --map-dir "$MAPDIR" \
    --resolution "$RES" --output "$FIGURE" \
    --west "$WEST" --east "$EAST" --south "$SOUTH" --north "$NORTH" \
    --depth-min "$DEPTH_MIN" --depth-max "$DEPTH_MAX" \
    --figure-width "$FIGURE_WIDTH" --figure-height "$FIGURE_HEIGHT" --dpi "$DPI"

printf '\n[SUCCESS] Created flood-depth comparison Figure.\n'
printf 'Figure: %s\n' "$FIGURE"
