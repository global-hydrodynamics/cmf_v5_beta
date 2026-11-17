#!/bin/sh
# Convert selected map-root Binary files to individual NetCDF files.
# Inputs: bin2nc_list.txt in the current working directory, params.txt, registered .bin files.
# Outputs: <map>/netcdf/<binary-stem>.nc.
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
STEP="Read and validate the selected conversion list"
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

# --map-dir is explicit; otherwise require a map-local script_bin2nc/ current directory.
FORCE=0
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
        --force) FORCE=1; shift ;;
        --help|-h)
            printf 'Usage: %s [--map-dir PATH] [--force]\n' "$SCRIPT_NAME"
            exit 0
            ;;
        *)
            printf 'Usage: %s [--map-dir PATH] [--force]\n' "$SCRIPT_NAME" >&2
            exit 2
            ;;
    esac
done

if [ -z "$MAP_DIR" ]; then
    # Shell suffix removal gives the last directory component without invoking basename.
    if [ "${RUN_DIR##*/}" != script_bin2nc ]; then
        printf 'ERROR: run from <map>/script_bin2nc/ or supply --map-dir PATH.\n' >&2
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
    printf 'ERROR: map/tools/script_bin2nc is a template, not a map. Run from a map-local directory or supply --map-dir PATH.\n' >&2
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
NETCDF_DIR="$MAP_DIR/netcdf"

if [ ! -f "$LIST_FILE" ]; then
    printf 'ERROR: conversion list not found: %s\n' "$LIST_FILE" >&2
    printf 'Run s01-list_binary.sh first.\n' >&2
    exit 1
fi

FILE_COUNT=0
SEEN_FILES=""
while IFS= read -r FILE || [ -n "$FILE" ]; do
    case "$FILE" in
        ""|\#*)
            continue
            ;;
    esac

    case "$FILE" in
        *.bin)
            ;;
        *)
            printf 'ERROR: invalid list entry (expected a .bin filename): %s\n' "$FILE" >&2
            exit 1
            ;;
    esac
    case "$FILE" in
        *[!a-zA-Z0-9_.-]*)
            printf 'ERROR: invalid or non-base filename in conversion list: %s\n' "$FILE" >&2
            exit 1
            ;;
    esac
    if [ ! -f "$MAP_DIR/$FILE" ]; then
        printf 'ERROR: listed Binary file does not exist: %s\n' "$MAP_DIR/$FILE" >&2
        exit 1
    fi
    case " $SEEN_FILES " in
        *" $FILE "*)
            printf 'ERROR: duplicate file in conversion list: %s\n' "$FILE" >&2
            exit 1
            ;;
    esac
    SEEN_FILES="$SEEN_FILES $FILE"
    FILE_COUNT=$((FILE_COUNT + 1))
done < "$LIST_FILE"

if [ "$FILE_COUNT" -eq 0 ]; then
    printf 'ERROR: no files are selected in %s.\n' "$LIST_FILE" >&2
    exit 1
fi

mkdir -p "$NETCDF_DIR"
CONVERTED=0
SKIPPED=0
FILE_NUMBER=0
STEP="Convert selected Binary map files"

# Keep the list on file descriptor 3 so overwrite prompts still read stdin.
while IFS= read -r FILE <&3 || [ -n "$FILE" ]; do
    case "$FILE" in
        ""|\#*)
            continue
            ;;
    esac

    FILE_NUMBER=$((FILE_NUMBER + 1))
    OUTPUT_FILE="$NETCDF_DIR/${FILE%.bin}.nc"
    printf '\n==================================================\n'
    printf '[STEP %s/%s] Convert %s\n' "$FILE_NUMBER" "$FILE_COUNT" "$FILE"
    printf '==================================================\n\n'

    # Interactive approval applies only to this file, not the remaining list.
    OVERWRITE=$FORCE
    if [ -f "$OUTPUT_FILE" ] && [ "$FORCE" -eq 0 ]; then
        if [ ! -t 0 ]; then
            printf 'Existing output preserved in non-interactive mode: %s\n' "$OUTPUT_FILE"
            SKIPPED=$((SKIPPED + 1))
            continue
        fi

        while :; do
            printf '%s already exists.\nOverwrite? [y/N]: ' "$OUTPUT_FILE"
            if ! IFS= read -r ANSWER; then
                ANSWER=""
            fi
            case "$ANSWER" in
                y|Y)
                    OVERWRITE=1
                    break
                    ;;
                ""|n|N)
                    printf 'Skipping %s.\n' "$FILE"
                    SKIPPED=$((SKIPPED + 1))
                    continue 2
                    ;;
                *)
                    printf 'Please answer y or N.\n' >&2
                    ;;
            esac
        done
    fi

    if [ "$OVERWRITE" -eq 1 ]; then
        python3 "$CONVERTER" \
            --map-dir "$MAP_DIR" \
            --registry "$REGISTRY" \
            --input "$MAP_DIR/$FILE" \
            --output "$OUTPUT_FILE" \
            --force
    else
        python3 "$CONVERTER" \
            --map-dir "$MAP_DIR" \
            --registry "$REGISTRY" \
            --input "$MAP_DIR/$FILE" \
            --output "$OUTPUT_FILE"
    fi
    CONVERTED=$((CONVERTED + 1))
done 3< "$LIST_FILE"

printf '\nConverted: %s; skipped: %s\n' "$CONVERTED" "$SKIPPED"
printf '\n==================================================\n'
printf '[SUCCESS] %s\n' "$SCRIPT_NAME"
printf '==================================================\n'
