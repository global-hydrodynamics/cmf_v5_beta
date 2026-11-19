#!/bin/bash
# Extract independent annual Mekong files using the shared Python tool.
set -eu

# User settings

# Dataset settings: inclusive years and grid-cell boundaries in degrees east/north.
START_YEAR=1979
END_YEAR=2010
WEST=90
EAST=110
SOUTH=5
NORTH=35
JOBS=4

# Command substitution locates this script independently of the caller's directory.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
INPUT_DIR="$SCRIPT_DIR/../ELSE_GPCC"
OUTPUT_DIR="$SCRIPT_DIR"

# ================================================================
# User settings end here
# ================================================================

usage() {
    cat <<'HELP'
Usage: s00-extract_ELSE_GPCC.sh [options]
  --input-dir DIR   Global annual NetCDF input (default: ../ELSE_GPCC)
  --output-dir DIR  Output directory (default: beside this script)
  --start-year N    First year, inclusive (default: 1979)
  --end-year N      Last year, inclusive (default: 2010)
  --jobs N          Maximum concurrent extractions (default: 4; 1 is sequential)
  --help           Show this help
Existing output files are never overwritten. Use a Python environment with
NumPy and netCDF4; the shared extractor is invoked with python3 from PATH.
HELP
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --help|-h) usage; exit 0 ;;
        --input-dir|--output-dir|--start-year|--end-year|--jobs)
            if [ "$#" -lt 2 ]; then
                printf '[ERROR] Missing value for %s\n' "$1" >&2
                exit 2
            fi
            case "$1" in
                --input-dir) INPUT_DIR=$2 ;;
                --output-dir) OUTPUT_DIR=$2 ;;
                --start-year) START_YEAR=$2 ;;
                --end-year) END_YEAR=$2 ;;
                --jobs) JOBS=$2 ;;
            esac
            shift 2
            ;;
        *) printf '[ERROR] Unknown option: %s\n' "$1" >&2; exit 2 ;;
    esac
done

for value in "$START_YEAR" "$END_YEAR" "$JOBS"; do
    if ! [[ "$value" =~ ^[1-9][0-9]*$ ]] || [ "${#value}" -gt 9 ]; then
        printf '[ERROR] Years and jobs must be positive decimal integers.\n' >&2
        exit 2
    fi
done
if [ "$START_YEAR" -gt "$END_YEAR" ] || [ "$END_YEAR" -ge 9999 ]; then
    printf '[ERROR] Require 1 <= start-year <= end-year < 9999.\n' >&2
    exit 2
fi

# Keep per-year output together; the private temporary logs are removed on exit.
LOG_DIR=$(mktemp -d "${TMPDIR:-/tmp}/cmf-mekong-extract.XXXXXX")
PIDS=()
YEARS=()
FAILED_YEARS=""

cleanup() {
    # Stop outstanding children if the wrapper is interrupted, then release logs.
    if [ "${#PIDS[@]}" -gt 0 ]; then
        for pid in "${PIDS[@]}"; do
            kill "$pid" 2>/dev/null || true
        done
    fi
    wait || true
    rm -rf -- "$LOG_DIR"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
# End of error handling.

wait_batch() {
    local index year
    # Array indices pair each background PID with its year and log files.
    for index in "${!PIDS[@]}"; do
        year=${YEARS[$index]}
        if wait "${PIDS[$index]}"; then
            printf '\n[SUCCESS] Year %s\n' "$year"
        else
            printf '\n[ERROR] Year %s\n' "$year" >&2
            FAILED_YEARS="$FAILED_YEARS $year"
        fi
        unset 'PIDS[index]'
        cat "$LOG_DIR/$year.out"
        cat "$LOG_DIR/$year.err" >&2
    done
    PIDS=()
    YEARS=()
}

printf '\n[STEP 1/1] Extracting years %s–%s with up to %s workers\n' "$START_YEAR" "$END_YEAR" "$JOBS"
for ((year=START_YEAR; year<=END_YEAR; year++)); do
    # Each child opens its own NetCDF files; no Python extraction logic is duplicated.
    printf -v year_tag '%04d' "$year"
    python3 "$SCRIPT_DIR/../tools/extract_ELSE_GPCC.py" \
        --input-dir "$INPUT_DIR" --output-dir "$OUTPUT_DIR" \
        --west "$WEST" --east "$EAST" --south "$SOUTH" --north "$NORTH" \
        --start-date "$year_tag-01-01" --end-date "$year_tag-12-31" \
        --format netcdf --file-unit year \
        > "$LOG_DIR/$year.out" 2> "$LOG_DIR/$year.err" &
    PIDS+=("$!")
    YEARS+=("$year")
    if [ "${#PIDS[@]}" -ge "$JOBS" ]; then
        wait_batch
    fi
done
if [ "${#PIDS[@]}" -gt 0 ]; then
    wait_batch
fi

if [ -n "$FAILED_YEARS" ]; then
    printf '\n[ERROR] Failed years:%s\n' "$FAILED_YEARS" >&2
    exit 1
fi
printf '\n[SUCCESS] Completed %s years\n' "$((END_YEAR - START_YEAR + 1))"
