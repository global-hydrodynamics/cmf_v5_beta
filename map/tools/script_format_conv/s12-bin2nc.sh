#!/bin/sh
# Convert selected registered Binary files into NetCDF files at ../.
# Run s11-list_bin.sh first; edit bin2nc_list.txt in this directory.
set -eu

# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
NO_OVERWRITE=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --no-overwrite) NO_OVERWRITE=1; shift ;;
        --force) NO_OVERWRITE=0; shift ;;
        --help|-h) printf 'Usage: ./%s [--no-overwrite]\n' "${0##*/}"; exit 0 ;;
        *) printf 'Usage: ./%s [--no-overwrite]\n' "${0##*/}" >&2; exit 2 ;;
    esac
done

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
REGISTRY="$CMF_V50_ROOT/variable_table/map_variables.csv"
LIST_FILE="bin2nc_list.txt"
BINARY_DIR="../binary"
NETCDF_DIR=".."

cmf_check_init "Convert selected base-map Binary files to NetCDF"
[ -f ../params.toml ] || [ -f ../params.txt ] || { printf 'Map-root params.toml/params.txt is missing.\n' >&2; exit 1; }
[ -f "$LIST_FILE" ] || { printf 'Conversion list missing; run s11-list_bin.sh first.\n' >&2; exit 1; }

FILE_COUNT=0
SEEN=""
while IFS= read -r FILE || [ -n "$FILE" ]; do
    case "$FILE" in ''|\#*) continue ;; esac
    case "$FILE" in *.bin) ;; *) printf 'Invalid list entry (expected .bin): %s\n' "$FILE" >&2; exit 1 ;; esac
    case "$FILE" in *[!a-zA-Z0-9_.-]*) printf 'Invalid base filename: %s\n' "$FILE" >&2; exit 1 ;; esac
    [ -f "$BINARY_DIR/$FILE" ] || { printf 'Listed Binary file missing: %s\n' "$BINARY_DIR/$FILE" >&2; exit 1; }
    case " $SEEN " in *" $FILE "*) printf 'Duplicate file in conversion list: %s\n' "$FILE" >&2; exit 1 ;; esac
    SEEN="$SEEN $FILE"
    FILE_COUNT=$((FILE_COUNT + 1))
done < "$LIST_FILE"
[ "$FILE_COUNT" -gt 0 ] || { printf 'No files selected in %s.\n' "$LIST_FILE" >&2; exit 1; }

cmf_check_step 1 1 "Convert the $FILE_COUNT selected Binary map files"
FILE_NUMBER=0
CONVERTED=0
SKIPPED=0
for FILE in $SEEN; do
    FILE_NUMBER=$((FILE_NUMBER + 1))
    OUTPUT_FILE="$NETCDF_DIR/${FILE%.bin}.nc"
    printf '[%s/%s] %s -> %s\n' "$FILE_NUMBER" "$FILE_COUNT" "$BINARY_DIR/$FILE" "$OUTPUT_FILE"
    set --
    case "$FILE" in
        mpireg-*.bin)
            MPI_COUNT=${FILE#mpireg-}; MPI_COUNT=${MPI_COUNT%.bin}
            case "$MPI_COUNT" in *[1-9]*) set -- --reference-binary mpireg.bin ;; esac ;;
    esac
    if [ -f "$OUTPUT_FILE" ] && [ "$NO_OVERWRITE" -eq 1 ]; then
        printf 'Existing output preserved: %s\n' "$OUTPUT_FILE"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi
    if [ "$NO_OVERWRITE" -eq 1 ]; then
        "$PYTHON_CMD" "$CODE_DIR/convert_map_binary_to_netcdf.py" --map-dir .. \
            --registry "$REGISTRY" --input "$BINARY_DIR/$FILE" --output "$OUTPUT_FILE" "$@"
    else
        "$PYTHON_CMD" "$CODE_DIR/convert_map_binary_to_netcdf.py" --map-dir .. \
            --registry "$REGISTRY" --input "$BINARY_DIR/$FILE" --output "$OUTPUT_FILE" "$@" --force
    fi
    CONVERTED=$((CONVERTED + 1))
done
printf 'Converted: %s; skipped: %s\n' "$CONVERTED" "$SKIPPED"

cmf_check_success

# Optional shell flag: --no-overwrite preserves existing NetCDF outputs.
