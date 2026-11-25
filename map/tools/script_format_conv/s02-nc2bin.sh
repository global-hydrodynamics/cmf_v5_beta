#!/bin/sh
# Convert selected registered base-map NetCDF files into map/binary/.
set -eu

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
REPO_ROOT=$(CDPATH= cd "$SCRIPT_DIR/../../.." && pwd -P)
RUN_DIR=$(pwd -P)
MAP_DIR=""
LIST_FILE="$RUN_DIR/nc2bin_list.txt"
NO_OVERWRITE=0

while [ "$#" -gt 0 ]; do
    case "$1" in
        --map-dir) [ "$#" -ge 2 ] || { echo 'ERROR: --map-dir requires a path.' >&2; exit 2; }; MAP_DIR=$2; shift 2 ;;
        --no-overwrite) NO_OVERWRITE=1; shift ;;
        --help|-h) echo "Usage: ${0##*/} [--map-dir PATH] [--no-overwrite]"; exit 0 ;;
        *) echo "Usage: ${0##*/} [--map-dir PATH] [--no-overwrite]" >&2; exit 2 ;;
    esac
done
if [ -z "$MAP_DIR" ]; then
    [ "${RUN_DIR##*/}" = script_format_conv ] || { echo 'ERROR: run from <map>/script_format_conv/ or pass --map-dir.' >&2; exit 2; }
    MAP_DIR="$RUN_DIR/.."
fi
MAP_DIR=$(CDPATH= cd "$MAP_DIR" && pwd -P)
[ -f "$MAP_DIR/params.txt" ] || { echo "ERROR: params.txt not found in $MAP_DIR" >&2; exit 1; }
[ -f "$LIST_FILE" ] || { echo "ERROR: $LIST_FILE not found; run s01-list_nc.sh first." >&2; exit 1; }

COUNT=0
SEEN=""
while IFS= read -r FILE || [ -n "$FILE" ]; do
    case "$FILE" in ''|\#*) continue ;; esac
    case "$FILE" in *.nc) ;; *) echo "ERROR: expected a base .nc filename: $FILE" >&2; exit 1 ;; esac
    case "$FILE" in */*|*[!a-zA-Z0-9_.-]*) echo "ERROR: invalid base filename: $FILE" >&2; exit 1 ;; esac
    case " $SEEN " in *" $FILE "*) echo "ERROR: duplicate source: $FILE" >&2; exit 1 ;; esac
    [ -f "$MAP_DIR/$FILE" ] || { echo "ERROR: NetCDF source missing: $MAP_DIR/$FILE" >&2; exit 1; }
    SEEN="$SEEN $FILE"
    COUNT=$((COUNT + 1))
done < "$LIST_FILE"
[ "$COUNT" -gt 0 ] || { echo "ERROR: no files selected in $LIST_FILE" >&2; exit 1; }

mkdir -p "$MAP_DIR/binary"
NUMBER=0
for FILE in $SEEN; do
    NUMBER=$((NUMBER + 1))
    OUTPUT="$MAP_DIR/binary/${FILE%.nc}.bin"
    echo "[$NUMBER/$COUNT] $FILE -> $OUTPUT"
    set --
    [ "$NO_OVERWRITE" -eq 0 ] || set -- --no-overwrite
    python3 "$REPO_ROOT/map/tools/code/convert_map_netcdf_to_binary.py" \
        --map-dir "$MAP_DIR" --input "$MAP_DIR/$FILE" --output "$OUTPUT" \
        --registry "$REPO_ROOT/variable_table/map_variables.csv" "$@"
done
echo "Converted $COUNT NetCDF map file(s) to Binary."
