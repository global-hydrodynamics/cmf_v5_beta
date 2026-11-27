#!/bin/sh
# Convert the selected registered base-map NetCDF files to ../binary/.
# Run s01-list_nc.sh first; edit nc2bin_list.txt in this directory.
set -eu

# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
NO_OVERWRITE=""   # Set to "--no-overwrite" to preserve existing files.

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
REGISTRY="$CMF_V50_ROOT/variable_table/map_variables.csv"
LIST_FILE="nc2bin_list.txt"
BINARY_DIR="../binary"

cmf_check_init "Convert selected base-map NetCDF files to Binary"
[ -f "$LIST_FILE" ] || { printf 'Conversion list missing; run s01-list_nc.sh first.\n' >&2; exit 1; }
[ -f ../params.toml ] || [ -f ../params.txt ] || { printf 'Map-root params.toml/params.txt is missing.\n' >&2; exit 1; }

COUNT=0
SEEN=""
while IFS= read -r FILE || [ -n "$FILE" ]; do
    case "$FILE" in ''|\#*) continue ;; esac
    case "$FILE" in *.nc) ;; *) printf 'Expected a base .nc filename: %s\n' "$FILE" >&2; exit 1 ;; esac
    case "$FILE" in */*|*[!a-zA-Z0-9_.-]*) printf 'Invalid base filename: %s\n' "$FILE" >&2; exit 1 ;; esac
    case " $SEEN " in *" $FILE "*) printf 'Duplicate source: %s\n' "$FILE" >&2; exit 1 ;; esac
    [ -f "../$FILE" ] || { printf 'NetCDF source missing: ../%s\n' "$FILE" >&2; exit 1; }
    SEEN="$SEEN $FILE"
    COUNT=$((COUNT + 1))
done < "$LIST_FILE"
[ "$COUNT" -gt 0 ] || { printf 'No files selected in %s.\n' "$LIST_FILE" >&2; exit 1; }
mkdir -p "$BINARY_DIR"

cmf_check_step 1 1 "Convert the $COUNT selected NetCDF map files"
NUMBER=0
for FILE in $SEEN; do
    NUMBER=$((NUMBER + 1))
    OUTPUT="$BINARY_DIR/${FILE%.nc}.bin"
    printf '[%s/%s] ../%s -> %s\n' "$NUMBER" "$COUNT" "$FILE" "$OUTPUT"
    # Intentionally unquoted: empty adds no argument; otherwise forward the option.
    "$PYTHON_CMD" "$CODE_DIR/convert_map_netcdf_to_binary.py" \
        --map-dir .. --input "../$FILE" --output "$OUTPUT" \
        --registry "$REGISTRY" $NO_OVERWRITE
done

cmf_check_success
