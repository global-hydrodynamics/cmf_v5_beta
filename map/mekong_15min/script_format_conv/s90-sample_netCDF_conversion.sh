#!/bin/bash
# Convert explicitly named experimental Binary maps using standard registry definitions.
# Shared template: map/tools/script_format_conv/s90-sample_netCDF_conversion.sh.
set -eu

# ============================================================
# User settings
# ============================================================

# Input Binary filename : Reference Binary filename
VARIANTS=(
    "subbsn-sample.bin:subbsn.bin"
    "subcol-sample.bin:subcol.bin"
)

FORCE=0

# ============================================================
# User settings end here
# ============================================================

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
REPO_ROOT=$(CDPATH= cd "$SCRIPT_DIR/../../.." && pwd -P)
CONVERTER="$REPO_ROOT/map/tools/code/convert_map_binary_to_netcdf.py"
RUN_DIR=$(pwd -P)
MAP_DIR=""

SCRIPT_NAME=${0##*/}
STEP="Select variant map conversions"
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
        *) printf 'ERROR: unknown argument: %s\n' "$1" >&2; exit 2 ;;
    esac
done

if [ -z "$MAP_DIR" ]; then
    if [ "${RUN_DIR##*/}" != script_format_conv ]; then
        printf 'ERROR: run from <map>/script_format_conv/ or supply --map-dir PATH.\n' >&2
        exit 2
    fi
    MAP_DIR="$RUN_DIR/.."
fi
MAP_DIR=$(CDPATH= cd "$MAP_DIR" && pwd -P)
if [ "$MAP_DIR" = "$REPO_ROOT/map/tools" ]; then
    printf 'ERROR: map/tools/script_format_conv is a template, not a map; supply --map-dir PATH.\n' >&2
    exit 2
fi

set --
if [ "$FORCE" -eq 1 ]; then
    set -- --force
fi

NUMBER=0
for VARIANT in "${VARIANTS[@]}"; do
    # Only literal base filenames are settings here; metadata lives in the CSV.
    case "$VARIANT" in
        *:*) INPUT=${VARIANT%%:*}; REFERENCE=${VARIANT#*:} ;;
        *) printf 'ERROR: expected input.bin:reference.bin: %s\n' "$VARIANT" >&2; exit 2 ;;
    esac
    case "$INPUT:$REFERENCE" in
        */*|*:*:*) printf 'ERROR: expected two base filenames: %s\n' "$VARIANT" >&2; exit 2 ;;
    esac
    case "$INPUT" in
        *.bin) ;;
        *) printf 'ERROR: expected an input .bin filename: %s\n' "$INPUT" >&2; exit 2 ;;
    esac
    NUMBER=$((NUMBER + 1))
    STEP="Convert $INPUT using $REFERENCE"
    printf '\n==================================================\n[STEP %s/%s] %s\n==================================================\n\n' "$NUMBER" "${#VARIANTS[@]}" "$STEP"

    python3 "$CONVERTER" \
        --map-dir "$MAP_DIR" \
        --input "$MAP_DIR/$INPUT" \
        --output "$MAP_DIR/netcdf/${INPUT%.bin}.nc" \
        --reference-binary "$REFERENCE" \
        "$@"
done

printf '\n==================================================\n[SUCCESS] %s\n==================================================\n' "$SCRIPT_NAME"
