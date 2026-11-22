#!/bin/sh
# Generate the Rhine regional ERA5-Land runoff-to-map correspondence matrix.
set -eu

# Paths
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
MAP_DIR=$(CDPATH= cd "$SCRIPT_DIR/.." && pwd -P)
CODE_DIR=$(CDPATH= cd "$SCRIPT_DIR/../../tools/code" && pwd -P)

# User settings
ROFFTAG="ERA5land_Rhine2021Jul"
GRSIZEIN=0.1
WESTIN=2.45
EASTIN=13.55
NORTHIN=53.55
SOUTHIN=44.45
OLAT="NtoS"
HIRES_TAG="1min"

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------

DIMINFO="diminfo_${ROFFTAG}.txt"
INPMAT="inpmat_${ROFFTAG}.bin"
EXEC_INPMAT="$CODE_DIR/param_inpmat_generate"
SCRIPT_NAME=${0##*/}
STEP="Generate regional runoff input matrix"

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

cd "$MAP_DIR"

STEP="Map the 1-minute catchment assignment to the regional runoff grid"
printf '\n==================================================\n[STEP 1/1] Generate Rhine runoff input matrix\n==================================================\n\n'
"$EXEC_INPMAT" "$HIRES_TAG" "$GRSIZEIN" "$WESTIN" "$EASTIN" \
    "$NORTHIN" "$SOUTHIN" "$OLAT" "$DIMINFO" "$INPMAT"

printf '\n==================================================\n[SUCCESS] %s\n==================================================\n' "$SCRIPT_NAME"
