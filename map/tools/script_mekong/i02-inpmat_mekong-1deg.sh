#!/bin/sh
set -eu

# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
# Runoff grid and output tag; these describe runoff data, not the river map grid.
ROFFTAG="repo-mek_1deg"  # Runoff sample ID used in the paired output filenames.
GRSIZEIN=1                # Runoff grid-cell size (degrees).
WESTIN=90                 # Western boundary (degrees longitude).
EASTIN=110                # Eastern boundary (degrees longitude).
NORTHIN=35                # Northern boundary (degrees latitude).
SOUTHIN=5                 # Southern boundary (degrees latitude).
OLAT="NtoS"               # Runoff latitude rows are ordered north to south.

HIRES_TAG=""  # Empty selects the coarsest installed map; set a tag to choose explicitly.
# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"

cmf_check_init "Generate the standard runoff input matrix"

AVAILABLE=""
if [ -z "$HIRES_TAG" ]; then
    for tag in 1min 30sec 15sec 5sec 3sec 1sec; do
        if [ -d "../$tag" ]; then
            AVAILABLE="${AVAILABLE}${AVAILABLE:+ }$tag"
            [ -n "$HIRES_TAG" ] || HIRES_TAG=$tag
        fi
    done
    [ -n "$HIRES_TAG" ] || { printf 'No high-resolution map found in the map root.\n' >&2; exit 1; }
    printf 'Selected high-resolution map: ../%s\n' "$HIRES_TAG"
    while :; do
        printf 'Use this map? [Y/n]: '
        IFS= read -r answer
        case "$answer" in
            ''|y|Y|yes|Yes|YES) break ;;
            n|N|no|No|NO)
                while :; do
                    printf 'Available resolutions: %s\nChoose resolution: ' "$AVAILABLE"
                    IFS= read -r HIRES_TAG
                    case " $AVAILABLE " in *" $HIRES_TAG "*) break 2 ;; esac
                    printf 'Choose one of the listed resolutions.\n'
                done ;;
            *) printf 'Please answer Yes or No (Enter = Yes).\n' ;;
        esac
    done
fi

cmf_check_step 1 1 "Map river cells to the configured runoff grid"
"$PYTHON_CMD" "$CODE_DIR/param_inpmat_generate.py" "$HIRES_TAG" "$GRSIZEIN" \
    "$WESTIN" "$EASTIN" "$NORTHIN" "$SOUTHIN" "$OLAT" \
    "diminfo_${ROFFTAG}.nml" "inpmat_${ROFFTAG}.nc" --map-dir ..

cmf_check_success

# Optional Python CLI flags: add --map-format binary to use legacy Binary maps.
