#!/bin/sh
# Generate numeric visualization caches; source NetCDF files remain authoritative.
# Run from <map>/script_format_conv/ or pass --map-dir PATH from another directory.
set -eu

# -------------------------- User settings ------------------------------
RESOLUTIONS="base 1min"        # Model grid and native high-res tags; global/Mekong: base 1min.
VARS="all"                     # All registered products, or space-separated file stems.
BLOCKSIZE=512                  # TIFF tile edge [pixels], 128..4096 and divisible by16.
COMPRESSION="DEFLATE"          # Lossless DEFLATE, LZW, ZSTD or NONE.
OVERVIEWS="2 4 8 16 32"        # Display-only reduction factors; small inputs omit excess levels.
JOBS=4                         # Independent file workers; each has a bounded GDAL cache.

# ----------------------------------------------------------------------
# User settings end here. Shared program paths and processing follow.
# ----------------------------------------------------------------------

# CDPATH= ignores user cd search paths; command substitution captures the physical path.
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
REPO_ROOT=$(CDPATH= cd "$SCRIPT_DIR/../../.." && pwd -P)
SCRIPT_NAME=${0##*/} # Shell suffix removal gives this script's basename.
STEP="Generate verified numeric COG files"
trap '
    EXIT_STATUS=$?
    trap - 0
    if [ "$EXIT_STATUS" -ne 0 ]; then
        printf "\n[ERROR] %s failed during: %s (exit %s)\n" "$SCRIPT_NAME" "$STEP" "$EXIT_STATUS" >&2
    fi
    exit "$EXIT_STATUS"
' 0
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
# End of error handling.

printf '\n==================================================\n[STEP 1/1] Convert NetCDF maps to COG\n==================================================\n\n'
# Python owns argument parsing, source checks and implicit map-local target resolution.
python3 "$REPO_ROOT/map/tools/code/convert_netcdf_to_cog.py" \
    --resolutions "$RESOLUTIONS" --variables "$VARS" \
    --blocksize "$BLOCKSIZE" --compression "$COMPRESSION" \
    --overviews "$OVERVIEWS" --jobs "$JOBS" "$@"
printf '\n[SUCCESS] Selected NetCDF-to-COG conversion completed.\n'
