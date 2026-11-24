#!/bin/sh
# Runoff-grid preset: calculate -> daily coastal modification -> mm/s export.
# Each stage is also callable alone; Python owns calendar, units, I/O and validation.
set -eu

# User settings
DATASET="ELSE_GPCC"
INPUT_PATTERN="runoffYYYY.nc"  # Also accepts MM/DD or strftime date tokens and globs.
RUNOFF_VARIABLE="runoff"
START_YEAR=1981
END_YEAR=2010
INPUT_UNITS="auto"           # Read NetCDF units; unknown meanings cause an error.
INTERVAL_HOURS=""            # Optional explicit interval for files without time bounds.
COAST_MODIFICATION="yes"     # yes: correct source days then recompute climatology.
COAST_METHOD="minimum"       # Legacy daily minimum; not minimum of the mean field.
LONGITUDE_BOUNDARY="auto"    # Full 360-degree grids wrap; regional grids do not.
OUTPUT_PREFIX="ELSE_GPCC"
PYTHON_CMD="${PYTHON_CMD:-python3}"

# Command substitution resolves the workflow's location independently of the caller.
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
CMF_BASE=$(CDPATH= cd "$SCRIPT_DIR/../../.." && pwd -P)
INPUT_DIR="$CMF_BASE/inp/ELSE_GPCC"
OUTPUT_DIR="$SCRIPT_DIR/output"
REFERENCE="$CMF_BASE/map/data/ELSE_GPCC_clm-1981-2010.one"  # Set empty for another product/grid.

# ================================================================
# User settings end here. Optional first argument: all/calculate/modify/export.
# ================================================================

STAGE="all"
if [ "$#" -gt 0 ]; then
    STAGE=$1
    shift
fi
case "$STAGE" in
    all|calculate|modify|export) ;;
    *) echo "Usage: $0 [all|calculate|modify|export] [--overwrite]" >&2; exit 2 ;;
esac

# The exit trap reports a failed stage without changing the program's exit status.
trap 'status=$?; if [ "$status" -ne 0 ]; then printf "\n[ERROR] Runoff preset failed at %s (status %s)\n" "$STAGE" "$status" >&2; fi' 0

# ================================================================
# End of error handling.
# ================================================================

# set -- builds a safely quoted argument list; trailing explicit options can override settings.
set -- --dataset "$DATASET" --input-dir "$INPUT_DIR" --input-pattern "$INPUT_PATTERN" \
    --runoff-variable "$RUNOFF_VARIABLE" --start-year "$START_YEAR" --end-year "$END_YEAR" \
    --input-units "$INPUT_UNITS" --output-dir "$OUTPUT_DIR" --output-prefix "$OUTPUT_PREFIX" \
    --coast-modification "$COAST_MODIFICATION" "$@"
if [ -n "$INTERVAL_HOURS" ]; then
    set -- "$@" --interval-hours "$INTERVAL_HOURS"
fi

if [ -n "$REFERENCE" ]; then
    set -- "$@" --compare-reference "$REFERENCE"
fi

CODE_DIR="$CMF_BASE/map/tools/code"

if [ "$STAGE" = all ] || [ "$STAGE" = calculate ]; then
    printf '\n[STEP 1/3] Daily climatology and uncorrected long-term mean\n'
    "$PYTHON_CMD" -B "$CODE_DIR/runoff_calc_climatology.py" calculate "$@"
fi

if [ "$STAGE" = all ] || [ "$STAGE" = modify ]; then
    if [ "$COAST_MODIFICATION" = yes ]; then
        printf '\n[STEP 2/3] Minimum-neighbor correction of source days, then re-average\n'
        "$PYTHON_CMD" -B "$CODE_DIR/runoff_modify_coastal.py" "$@" \
            --method "$COAST_METHOD" --longitude-boundary "$LONGITUDE_BOUNDARY"
    fi
fi

if [ "$STAGE" = all ] || [ "$STAGE" = export ]; then
    printf '\n[STEP 3/3] Export long-term mean [mm/s] as NetCDF/Binary\n'
    "$PYTHON_CMD" -B "$CODE_DIR/runoff_calc_climatology.py" export "$@"
fi

printf '\n[SUCCESS] Runoff preset stage %s completed; output: %s\n' "$STAGE" "$OUTPUT_DIR"
