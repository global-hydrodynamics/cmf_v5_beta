#!/bin/sh
# Estimate permanent-water area per CaMa-Flood unit catchment.
# Copy to <map>/script_params/ and run from any working directory.
#
# Inputs: params.txt, nextxy.bin, ctmare.bin, and
#         <HIRES_TAG>/location.txt plus each area's catmxy, rivwth, flddif,
#         and optional grdare binary files.
# Output: prmwat.bin (float32, NX x NY, one record, m2) in the map root.
set -eu

# Paths
# Command substitution stores the resolved path; CDPATH= keeps cd output predictable.
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
MAP_DIR=$(CDPATH= cd "$SCRIPT_DIR/.." && pwd -P)
CODE_DIR=$(CDPATH= cd "$SCRIPT_DIR/../../tools/code" && pwd -P)

# Resolution is selected interactively from installed Binary directories below.

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------

# ${0##*/} removes the directory portion of the script path for readable messages.
SCRIPT_NAME=${0##*/}
STEP="Prepare permanent-water area calculation"
# The exit trap reports failures and preserves status; signal traps use standard nonzero statuses.
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

EXEC_PRMWAT="$CODE_DIR/param_water_calc_prmwat"

# Offer the finest installed Binary resolution; Fortran validates its contents.
STEP="Select high-resolution map"
AVAILABLE=""
HIRES_TAG=""
for tag in 1sec 3sec 5sec 15sec 30sec 1min; do
    if [ -d "$MAP_DIR/$tag" ]; then
        AVAILABLE="${AVAILABLE}${AVAILABLE:+ }$tag"
        if [ -z "$HIRES_TAG" ]; then HIRES_TAG=$tag; fi
    fi
done
if [ -z "$HIRES_TAG" ]; then
    printf 'ERROR: No Binary high-resolution directory found in %s (1sec, 3sec, 5sec, 15sec, 30sec, 1min).\n' "$MAP_DIR" >&2
    exit 1
fi

printf 'Highest available resolution: %s (%s/%s)\n' "$HIRES_TAG" "$MAP_DIR" "$HIRES_TAG"
while :; do
    printf 'Use this high-resolution map? [Y/n]: '
    IFS= read -r answer
    case "$answer" in
        ""|y|Y|yes|Yes|YES) break ;;
        n|N|no|No|NO)
            while :; do
                printf 'Available resolutions: %s\nChoose resolution: ' "$AVAILABLE"
                IFS= read -r chosen
                for tag in $AVAILABLE; do
                    if [ "$chosen" = "$tag" ]; then
                        HIRES_TAG=$chosen
                        break 2
                    fi
                done
                printf 'Choose one of the listed resolutions.\n'
            done
            break
            ;;
        *) printf 'Please answer Yes or No (Enter = Yes).\n' ;;
    esac
done
printf 'Selected high-resolution map: %s/%s\n' "$MAP_DIR" "$HIRES_TAG"

# The program reads map inputs relative to the map root.
cd "$MAP_DIR"

STEP="Aggregate permanent-water pixels from $HIRES_TAG into unit catchments"
printf '\n==================================================\n[STEP 1/1] Estimate permanent-water area (%s)\n==================================================\n\n' "$HIRES_TAG"
# Fortran owns the tag/geometry/file validation as well as the aggregation.
"$EXEC_PRMWAT" "$HIRES_TAG"

printf '\n==================================================\n[SUCCESS] %s\n==================================================\n' "$SCRIPT_NAME"
