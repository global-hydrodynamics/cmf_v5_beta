#!/bin/sh
# Create an editable list of registered base-map Binary files for conversion.
# Inputs: <map>/params.txt, variable_table/map_variables.csv, and map-root .bin files.
# Output: bin2nc_list.txt in the current working directory.
set -eu

# No map-name setting is needed; target selection follows the working directory or --map-dir.
# Command substitution locates shared resources independently of the target map.
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
REPO_ROOT=$(CDPATH= cd "$SCRIPT_DIR/../../.." && pwd -P)
TOOL_DIR="$REPO_ROOT/map/tools/code"
REGISTRY="$REPO_ROOT/variable_table/map_variables.csv"
CONVERTER="$TOOL_DIR/convert_map_binary_to_netcdf.py"
# The physical current directory owns the list and supplies the implicit target.
RUN_DIR=$(pwd -P)
MAP_DIR=""
LIST_FILE="$RUN_DIR/bin2nc_list.txt"

SCRIPT_NAME=${0##*/}
STEP="Check the existing conversion list"
trap '
    EXIT_STATUS=$?
    trap - 0
    if [ "$EXIT_STATUS" -ne 0 ]; then
        printf "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n" >&2
        printf "!!! ERROR: %s FAILED !!!\n" "$SCRIPT_NAME" >&2
        printf "!!! Step: %s\n" "$STEP" >&2
        printf "!!! Exit status: %s\n" "$EXIT_STATUS" >&2
        printf "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n" >&2
    fi
    exit "$EXIT_STATUS"
' 0
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

# ----------------------------------------------------------------------
# End of error handling.
# ----------------------------------------------------------------------

# --map-dir is explicit; otherwise require a map-local script_format_conv/ current directory.
while [ "$#" -gt 0 ]; do
    case "$1" in
        --map-dir)
            if [ "$#" -lt 2 ] || [ -z "$2" ]; then
                printf 'ERROR: --map-dir requires a directory.\n' >&2
                exit 2
            fi
            MAP_DIR=$2
            shift 2
            ;;
        --help|-h)
            printf 'Usage: %s [--map-dir PATH]\n' "$SCRIPT_NAME"
            exit 0
            ;;
        *)
            printf 'Usage: %s [--map-dir PATH]\n' "$SCRIPT_NAME" >&2
            exit 2
            ;;
    esac
done

if [ -z "$MAP_DIR" ]; then
    # Shell suffix removal gives the last directory component without invoking basename.
    if [ "${RUN_DIR##*/}" != script_format_conv ]; then
        printf 'ERROR: run from <map>/script_format_conv/ or supply --map-dir PATH.\n' >&2
        exit 2
    fi
    MAP_DIR="$RUN_DIR/.."
fi
if [ ! -d "$MAP_DIR" ]; then
    printf 'ERROR: map directory does not exist: %s\n' "$MAP_DIR" >&2
    exit 1
fi
MAP_DIR=$(CDPATH= cd "$MAP_DIR" && pwd -P)
if [ "$MAP_DIR" = "$REPO_ROOT/map/tools" ]; then
    printf 'ERROR: map/tools/script_format_conv is a template, not a map. Run from a map-local directory or supply --map-dir PATH.\n' >&2
    exit 2
fi
if [ ! -f "$MAP_DIR/params.txt" ]; then
    printf 'ERROR: target is not a map directory (params.txt missing): %s\n' "$MAP_DIR" >&2
    exit 1
fi
if [ ! -f "$CONVERTER" ] || [ ! -f "$REGISTRY" ]; then
    printf 'ERROR: shared converter or variable registry not found under %s\n' "$REPO_ROOT" >&2
    exit 1
fi

if [ -f "$LIST_FILE" ]; then
    if [ ! -t 0 ]; then
        printf 'Existing conversion list preserved in non-interactive mode: %s\n' "$LIST_FILE"
        exit 0
    fi

    while :; do
        printf '\n%s already exists. Regenerate it? [y/N]: ' "$LIST_FILE"
        if ! IFS= read -r ANSWER; then
            ANSWER=""
        fi
        case "$ANSWER" in
            y|Y)
                break
                ;;
            ""|n|N)
                printf 'Keeping the existing conversion list.\n'
                exit 0
                ;;
            *)
                printf 'Please answer y or N.\n' >&2
                ;;
        esac
    done
fi

STEP="Generate the base-map conversion list"
printf '\n==================================================\n'
printf '[STEP 1/1] Generate conversion candidates\n'
printf '==================================================\n\n'
python3 "$CONVERTER" \
    --map-dir "$MAP_DIR" \
    --registry "$REGISTRY" \
    --generate-list \
    --list-file "$LIST_FILE"

printf '\n==================================================\n'
printf '[SUCCESS] %s\n' "$SCRIPT_NAME"
printf '==================================================\n'
