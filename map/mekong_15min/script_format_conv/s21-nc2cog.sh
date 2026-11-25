#!/bin/sh
# Generate numeric COG visualization caches; source NetCDF maps remain authoritative.
# Run from this map's script_format_conv/ directory.
set -eu

# CaMa-Flood general setting (check CMF root, import shell error checker)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
RESOLUTIONS="auto"        # Base map plus the first available 1min, 30sec or 15sec map.
VARS="all"                # All registered products, or selected file stems.
BLOCKSIZE=512             # TIFF tile edge [pixels], 128..4096 and divisible by 16.
COMPRESSION="DEFLATE"     # Lossless DEFLATE, LZW, ZSTD or NONE.
OVERVIEWS="2 4 8 16 32"   # Display-only reduction factors.
JOBS=4                    # Independent file workers.

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
REGISTRY="$CMF_V50_ROOT/variable_table/map_variables.csv"
cmf_check_init "Generate registered numeric COG caches"
cmf_check_step 1 1 "Convert the selected NetCDF map products to COG"
"$PYTHON_CMD" "$CODE_DIR/convert_netcdf_to_cog.py" --map-dir .. \
    --resolutions "$RESOLUTIONS" --variables "$VARS" \
    --blocksize "$BLOCKSIZE" --compression "$COMPRESSION" \
    --overviews "$OVERVIEWS" --jobs "$JOBS"
cmf_check_success
