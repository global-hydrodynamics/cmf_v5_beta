#!/bin/sh
# Generate registered GrADS CTLs beside Binary products in the map root.
# Run from this map's script_format_conv/ directory.
set -eu

# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
PYTHON_CMD="python3"

cmf_check_init "Write CTLs for registered Binary products"

# Preserve map-root parameters, Binary-side diminfo files and high-resolution locations.
[ -f ../params.toml ] || [ -f ../params.txt ] || { printf 'Map-root params.toml/params.txt is missing.\n' >&2; exit 1; }
mkdir -p ../binary
"$PYTHON_CMD" "$CODE_DIR/migrate_map_params.py" --map-dir .. --write-legacy binary/params.txt
for DIMINFO in ../diminfo_*.txt; do
    [ -f "$DIMINFO" ] || continue
    # Keep Binary-side descriptors paired with the converted Binary filenames.
    [ -f "../binary/${DIMINFO##*/}" ] || cp "$DIMINFO" "../binary/${DIMINFO##*/}"
done
for SOURCE_LOCATION in ../*/location.txt; do
    [ -f "$SOURCE_LOCATION" ] || continue
    RESOLUTION_DIR=${SOURCE_LOCATION%/location.txt}
    RESOLUTION=${RESOLUTION_DIR##*/}
    mkdir -p "../binary/$RESOLUTION"
    cp "$SOURCE_LOCATION" "../binary/$RESOLUTION/location.txt"
done

cmf_check_step 1 1 "Generate CTLs for base, high-resolution and named sample Binary products"
"$PYTHON_CMD" "$CODE_DIR/generate_ctl.py" --map-dir ../binary "$@"
for LOCATION in ../binary/*/location.txt; do
    [ -f "$LOCATION" ] || continue
    GRID_DIR=${LOCATION%/location.txt}
    RESOLUTION=${GRID_DIR##*/}
    SOURCE_LOCATION="../$RESOLUTION/location.txt"
    [ -f "$SOURCE_LOCATION" ] && cp "$SOURCE_LOCATION" "$LOCATION"
    "$PYTHON_CMD" "$CODE_DIR/generate_ctl.py" --map-dir "$GRID_DIR" "$@"
done
for ENTRY in "subbsn-sample.bin:subbsn.bin" "subcol-sample.bin:subcol.bin" "upbasin-*.bin:upbasin.bin"; do
    PATTERN=${ENTRY%%:*}
    REFERENCE=${ENTRY#*:}
    for BINARY in ../binary/$PATTERN; do
        [ -f "$BINARY" ] || continue
        "$PYTHON_CMD" "$CODE_DIR/generate_ctl.py" --map-dir ../binary \
            --input "${BINARY##*/}" --reference-binary "$REFERENCE" "$@"
    done
done

cmf_check_success

# Optional generator flags: --dry-run, --no-overwrite, --overwrite.
