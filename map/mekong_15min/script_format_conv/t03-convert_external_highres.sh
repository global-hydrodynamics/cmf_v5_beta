#!/bin/sh
# Convert selected high-resolution Binary products in an external data package.
# Run from this map/tools/script_format_conv/ directory; outputs remain beside the source map.
set -eu

# CaMa-Flood general setting (check CMF root, import shell error checker)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/code/cmf_check_shell_error.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
MAP_ROOT="/Users/yamadai/work/CaMa_v400/cmf_v400_data/map_full"
MAPS="glb_01min"
HIRES="15sec 3sec"
VARS="catmxy"
COMPRESSION_LEVEL=3
JOBS=16

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
REGISTRY="$CMF_V50_ROOT/variable_table/map_variables.csv"
cmf_check_init "Convert external high-resolution maps"
[ -d "$MAP_ROOT" ] || { printf 'External map root not found: %s\n' "$MAP_ROOT" >&2; exit 1; }
cmf_check_step 1 1 "Convert selected external high-resolution products"
for map in $MAPS; do
    MAP_DIR="$MAP_ROOT/$map"
    if [ ! -d "$MAP_DIR" ]; then
        printf '[SKIP] Map directory not found: %s\n' "$MAP_DIR"
        continue
    fi
    for resolution in $HIRES; do
        HIRES_DIR="$MAP_DIR/$resolution"
        if [ ! -d "$HIRES_DIR" ]; then
            printf '[SKIP] High-resolution directory not found: %s\n' "$HIRES_DIR"
            continue
        fi
        [ -f "$HIRES_DIR/location.txt" ] || { printf 'Missing location.txt: %s\n' "$HIRES_DIR" >&2; exit 1; }
        mkdir -p "$MAP_DIR/${resolution}_nc"
        cp "$HIRES_DIR/location.txt" "$MAP_DIR/${resolution}_nc/location.txt"
        printf 'Map=%s resolution=%s variables=%s\n' "$map" "$resolution" "$VARS"
        "$PYTHON_CMD" "$CODE_DIR/convert_highres_binary_to_netcdf.py" \
            --map-dir "$MAP_DIR" --hires "$resolution" --variables "$VARS" \
            --registry "$REGISTRY" --compression-level "$COMPRESSION_LEVEL" \
            --jobs "$JOBS" --force
    done
done
cmf_check_success
